from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.api.dominio_temporal import DomainException


def _json(status: int, detail: str, codigo: str | None = None, **extra):
    cuerpo = {"detail": detail, "codigo": codigo, **extra}
    return JSONResponse(status_code=status, content=cuerpo)


def registrar_manejadores(app: FastAPI) -> None:
    @app.exception_handler(DomainException)
    async def _dominio(_: Request, exc: DomainException):
        return _json(exc.status_code, str(exc), type(exc).__name__)

    @app.exception_handler(RequestValidationError)
    async def _validacion(_: Request, exc: RequestValidationError):
        errores = [
            {"campo": ".".join(str(x) for x in e["loc"]), "mensaje": e["msg"]}
            for e in exc.errors()
        ]
        return _json(
            400, "Solicitud mal formada", "RequestValidationError",
            errores=jsonable_encoder(errores),
        )
