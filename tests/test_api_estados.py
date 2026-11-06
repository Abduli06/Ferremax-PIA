import pytest
from fastapi.testclient import TestClient
from src.api.main import crear_app

from tests.conftest import buscar_operacion


def _op_procesable(svc):
    return buscar_operacion(svc, activo=True, autorizado=True)


def test_flujo_completo_200(client, svc):
    op = _op_procesable(svc)
    for accion, estado in [("aprobar", "APROBADO"), ("surtir", "SURTIDO"), ("entregar", "ENTREGADO")]:
        r = client.post(f"/operaciones/{op.id}/{accion}")
        assert r.status_code == 200, r.text
        assert r.json()["estado"] == estado
    nombres = [e["nombre"] for e in client.get(f"/operaciones/{op.id}").json()["eventos"]]
    assert nombres == ["OperacionAprobada", "OperacionSurtida", "OperacionEntregada"]


def test_aprobar_dos_veces_409(client, svc):
    op = _op_procesable(svc)
    assert client.post(f"/operaciones/{op.id}/aprobar").status_code == 200
    r = client.post(f"/operaciones/{op.id}/aprobar")
    assert r.status_code == 409 and r.json()["codigo"] == "TransicionInvalida"


def test_saltar_estado_409(client, svc):
    op = _op_procesable(svc)
    assert client.post(f"/operaciones/{op.id}/surtir").status_code == 409
    assert client.post(f"/operaciones/{op.id}/entregar").status_code == 409


def test_aprobar_actor_inactivo_422(client, svc):
    op = buscar_operacion(svc, activo=False)
    r = client.post(f"/operaciones/{op.id}/aprobar")
    assert r.status_code == 422 and "inactivo" in r.json()["detail"]
    assert client.get(f"/operaciones/{op.id}").json()["estado"] == "CREADO"


def test_aprobar_no_autorizada_422(client, svc):
    op = buscar_operacion(svc, activo=True, autorizado=False)
    r = client.post(f"/operaciones/{op.id}/aprobar")
    assert r.status_code == 422 and "autorizada" in r.json()["detail"]


def test_aprobar_sin_lineas_422(client, svc):
    nueva = client.post("/operaciones", json={"actor_id": "FER-C025", "lineas": []}).json()
    r = client.post(f"/operaciones/{nueva['id']}/aprobar")
    assert r.status_code == 422 and "líneas" in r.json()["detail"]


def test_cancelar_200_y_despues_no_se_aprueba(client, svc):
    op = _op_procesable(svc)
    r = client.post(f"/operaciones/{op.id}/cancelar", json={"motivo": "Cliente desistió"})
    assert r.status_code == 200
    assert r.json()["estado"] == "CANCELADO" and r.json()["motivo_cancelacion"] == "Cliente desistió"
    assert client.post(f"/operaciones/{op.id}/aprobar").status_code == 409


def test_cancelar_motivo_vacio_422(client, svc):
    op = _op_procesable(svc)
    assert client.post(f"/operaciones/{op.id}/cancelar", json={"motivo": "  "}).status_code == 422


def test_cancelar_sin_cuerpo_400(client, svc):
    op = _op_procesable(svc)
    assert client.post(f"/operaciones/{op.id}/cancelar", json={}).status_code == 400


def test_cancelar_desde_aprobado_409(client, svc):
    op = _op_procesable(svc)
    client.post(f"/operaciones/{op.id}/aprobar")
    assert client.post(f"/operaciones/{op.id}/cancelar", json={"motivo": "x"}).status_code == 409


@pytest.mark.parametrize("accion", ["aprobar", "surtir", "entregar"])
def test_estados_inexistente_404(client, accion):
    assert client.post(f"/operaciones/NOPE/{accion}").status_code == 404


def test_cancelar_inexistente_404(client):
    assert client.post("/operaciones/NOPE/cancelar", json={"motivo": "x"}).status_code == 404


def test_surtir_stock_insuficiente_409(client):
    r = client.post("/operaciones", json={"actor_id": "FER-C025",
                    "lineas": [{"recurso_id": "FER-P001", "cantidad": 14}]})  
    oid = r.json()["id"]
    client.post(f"/operaciones/{oid}/aprobar")
    r = client.post(f"/operaciones/{oid}/surtir")
    assert r.status_code == 409 and r.json()["codigo"] == "StockInsuficiente"
    assert client.get(f"/operaciones/{oid}").json()["estado"] == "APROBADO"


def test_surtir_recurso_deshabilitado_422(client):
    oid = client.post("/operaciones", json={"actor_id": "FER-C025",
                      "lineas": [{"recurso_id": "FER-P011", "cantidad": 1}]}).json()["id"]
    client.post(f"/operaciones/{oid}/aprobar")
    assert client.post(f"/operaciones/{oid}/surtir").status_code == 422


def test_crear_201(client):
    r = client.post("/operaciones", json={"actor_id": "FER-C025",
                    "lineas": [{"recurso_id": "FER-P001", "cantidad": 2}]})
    assert r.status_code == 201
    assert r.json()["id"] == "FER-O061" and r.json()["total"] in ("1224.00", "1224")
    assert client.get("/operaciones/FER-O061").status_code == 200


def test_crear_actor_inexistente_404(client):
    assert client.post("/operaciones", json={"actor_id": "NADIE"}).status_code == 404


def test_crear_recurso_inexistente_422(client):
    r = client.post("/operaciones", json={"actor_id": "FER-C025",
                    "lineas": [{"recurso_id": "ZZZ", "cantidad": 1}]})
    assert r.status_code == 422


def test_crear_cantidad_negativa_400(client):
    r = client.post("/operaciones", json={"actor_id": "FER-C025",
                    "lineas": [{"recurso_id": "FER-P001", "cantidad": -1}]})
    assert r.status_code == 400


def test_estado_persiste_tras_reiniciar_la_app(settings, svc, client):
    op = _op_procesable(svc)
    client.post(f"/operaciones/{op.id}/aprobar")
    otra = TestClient(crear_app(settings))  # misma BD, app nueva
    assert otra.get(f"/operaciones/{op.id}").json()["estado"] == "APROBADO"
