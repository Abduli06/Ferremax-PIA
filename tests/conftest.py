import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from src.api.config import Settings, normalizar_db_url
from src.api.main import crear_app

DATOS = Path(__file__).resolve().parent.parent / "datos"


@pytest.fixture
def db_url(tmp_path):
    return normalizar_db_url(os.getenv("TEST_DATABASE_URL", f"sqlite:///{tmp_path}/test.db"))


@pytest.fixture
def settings(db_url):
    return Settings(environment="test", database_url=db_url, data_dir=DATOS)


@pytest.fixture
def app(settings):
    app = crear_app(settings)
    app.state.servicio.reiniciar() 
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def svc(app):
    return app.state.servicio


def buscar_operacion(svc, **criterios):
    for op in sorted(svc._ops.values(), key=lambda o: o.id):
        if op.estado.value != "CREADO":
            continue
        if all(getattr(op.actor, k, getattr(op, k, None)) == v for k, v in criterios.items()):
            return op
    raise AssertionError(f"No hay operación con {criterios}")
