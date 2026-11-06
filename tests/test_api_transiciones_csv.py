import csv
from pathlib import Path

import pytest

RUTA = Path(__file__).resolve().parent.parent / "datos" / "transiciones_prueba.csv"
CASOS = list(csv.DictReader(RUTA.open(encoding="utf-8-sig"))) if RUTA.exists() else []


def _post(client, oid, accion, **kw):
    return client.post(f"/operaciones/{oid}/{accion}", **kw)


@pytest.mark.skipif(not CASOS, reason="falta datos/transiciones_prueba.csv")
@pytest.mark.parametrize("caso", CASOS, ids=[c["caso_id"] for c in CASOS])
def test_transicion(client, svc, caso):
    oid, accion = caso["operacion_id"], caso["accion_sugerida"]
    procesable = client.get(f"/operaciones/{oid}/evaluacion").json()["puede_procesarse"]
    esperado_aprobar = 200 if procesable else 422

    if accion == "aprobar":
        assert _post(client, oid, "aprobar").status_code == esperado_aprobar
    elif accion == "repetir_aprobacion":
        assert _post(client, oid, "aprobar").status_code == esperado_aprobar
        if procesable:
            assert _post(client, oid, "aprobar").status_code == 409
    elif accion == "saltar_estado":
        assert _post(client, oid, "surtir").status_code == 409
    elif accion == "cancelar":
        r = _post(client, oid, "cancelar", json={"motivo": "Prueba CSV"})
        assert r.status_code == 200 and r.json()["estado"] == "CANCELADO"
    elif accion == "completar":
        if procesable:
            for paso in ("aprobar", "surtir", "entregar"):
                r = _post(client, oid, paso)
                if r.status_code == 409 and paso == "surtir": 
                    break
                assert r.status_code == 200, r.text
        else:
            assert _post(client, oid, "aprobar").status_code == 422
    else:  # pragma: no cover
        pytest.fail(f"Acción no contemplada: {accion}")
