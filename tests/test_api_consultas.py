from tests.conftest import buscar_operacion


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "database": "ok", "environment": "test"}


def test_raiz_redirige_a_docs(client):
    r = client.get("/", follow_redirects=False)
    assert r.status_code in (302, 307)
    assert r.headers["location"] == "/docs"


def test_openapi_expone_rutas_clave(client):
    rutas = client.get("/openapi.json").json()["paths"]
    for ruta in ("/operaciones", "/operaciones/{operacion_id}/aprobar",
                 "/operaciones/{operacion_id}/cancelar", "/actores/{actor_id}/credito"):
        assert ruta in rutas


def test_listar_operaciones_200(client):
    r = client.get("/operaciones")
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["total"] == 60
    assert len(cuerpo["items"]) == 50


def test_listar_paginado_y_filtro_estado(client):
    r = client.get("/operaciones", params={"estado": "CREADO", "limit": 5, "offset": 55})
    assert r.status_code == 200
    assert len(r.json()["items"]) == 5
    assert client.get("/operaciones", params={"estado": "ENTREGADO"}).json()["total"] == 0


def test_listar_filtro_actor(client):
    r = client.get("/operaciones", params={"actor_id": "FER-C025"})
    assert r.status_code == 200
    assert all(i["actor_id"] == "FER-C025" for i in r.json()["items"])


def test_listar_estado_invalido_400(client):
    r = client.get("/operaciones", params={"estado": "VOLANDO"})
    assert r.status_code == 400
    assert r.json()["codigo"] == "RequestValidationError"


def test_detalle_total_es_suma_con_decimal(client):
    r = client.get("/operaciones/FER-O001")
    assert r.status_code == 200
    d = r.json()
    assert d["estado"] == "CREADO"
    assert sum(float(x["subtotal"]) for x in d["lineas"]) == float(d["total"])
    assert d["unidades"] == sum(x["cantidad"] for x in d["lineas"])


def test_detalle_inexistente_404(client):
    r = client.get("/operaciones/FER-O999")
    assert r.status_code == 404
    assert r.json()["codigo"] == "OperacionNoEncontrada"


def test_evaluacion_de_reglas(client, svc):
    op = buscar_operacion(svc, activo=True, autorizado=True)
    r = client.get(f"/operaciones/{op.id}/evaluacion")
    assert r.status_code == 200
    assert r.json()["puede_procesarse"] is True and r.json()["motivos"] == []


def test_evaluacion_inexistente_404(client):
    assert client.get("/operaciones/NOPE/evaluacion").status_code == 404


def test_credito_actor_200(client):
    r = client.get("/actores/FER-C025/credito")
    assert r.status_code == 200
    assert r.json()["credito_suspendido"] is False


def test_credito_actor_inactivo_suspendido(client, svc):
    inactivo = next(a for a in svc.actores.values() if not a.activo)
    r = client.get(f"/actores/{inactivo.id}/credito")
    assert r.status_code == 200 and r.json()["credito_suspendido"] is True


def test_credito_actor_inexistente_404(client):
    assert client.get("/actores/NADIE/credito").status_code == 404
