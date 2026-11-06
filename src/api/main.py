from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from src.api.config import Settings
from src.api.errores import registrar_manejadores
from src.api.persistencia_temporal import RepositorioSnapshots
from src.api.rutas import router
from src.api.servicio import ServicioOperaciones

DESCRIPCION = (
    "API REST de FerreMax (PIA Componentes de Lógica de Negocio).\n\n"
    "Flujo: `CREADO → APROBADO → SURTIDO → ENTREGADO`; cancelación: `CREADO → CANCELADO`.\n\n"
    "Errores: **400** solicitud mal formada · **404** no encontrado · "
    "**409** conflicto de estado/stock · **422** regla de negocio violada."
)


def crear_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.desde_entorno()
    app = FastAPI(title="FerreMax API", version="1.0.0", description=DESCRIPCION)
    app.state.settings = settings
    app.state.servicio = ServicioOperaciones(
        settings.data_dir, RepositorioSnapshots(settings.database_url)
    )
    registrar_manejadores(app)
    app.include_router(router)

    @app.get("/", include_in_schema=False)
    def raiz():
        return RedirectResponse("/docs")

    return app


app = crear_app()
