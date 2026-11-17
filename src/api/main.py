from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from src.api.config import Settings
from src.api.errores import registrar_manejadores
from src.api.persistencia_temporal import RepositorioSnapshots
from src.api.rutas import router
from src.api.servicio import ServicioOperaciones

BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = BASE_DIR / "frontend"
IMG_DIR = FRONTEND_DIR / "img"

DESCRIPCION = (
    "API REST de FerreMax (PIA Componentes de Lógica de Negocio).\n\n"
    "Flujo: `CREADO → APROBADO → SURTIDO → ENTREGADO`; cancelación: `CREADO → CANCELADO`.\n\n"
    "Errores: **400** solicitud mal formada · **404** no encontrado · "
    "**409** conflicto de estado/stock · **422** regla de negocio violada."
)


def crear_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.desde_entorno()
    app = FastAPI(title="FerreMax API", version="1.0.0", description=DESCRIPCION)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Garantiza que la carpeta exista siempre antes de montar StaticFiles
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    app.mount("/img", StaticFiles(directory=str(IMG_DIR)), name="img")

    app.state.settings = settings
    app.state.servicio = ServicioOperaciones(
        settings.data_dir, RepositorioSnapshots(settings.database_url)
    )
    registrar_manejadores(app)
    app.include_router(router)

    @app.get("/", include_in_schema=False)
    def raiz():
        return RedirectResponse("/docs")

    @app.get("/app", include_in_schema=False)
    def tienda_comercial():
        return FileResponse(FRONTEND_DIR / "index.html")

    @app.api_route("/reset-demo", methods=["GET", "POST"], include_in_schema=False)
    def reiniciar_datos_demo():
        repo = RepositorioSnapshots(app.state.settings.database_url)
        # Si el repositorio usa SQLAlchemy, limpia todas las tablas registradas
        if hasattr(repo, "_engine"):
            from sqlalchemy import MetaData
            meta = MetaData()
            meta.reflect(bind=repo._engine)
            with repo._engine.begin() as conn:
                for tabla in reversed(meta.sorted_tables):
                    conn.execute(tabla.delete())
        app.state.servicio = ServicioOperaciones(app.state.settings.data_dir, repo)
        return {"status": "ok", "mensaje": "Base de datos limpia y restaurada a los 60 pedidos originales"}

    return app


app = crear_app()