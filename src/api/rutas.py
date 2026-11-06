from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status

from src.api import schemas
from src.api.servicio import ServicioOperaciones

router = APIRouter()


def get_servicio(request: Request) -> ServicioOperaciones:
    return request.app.state.servicio


Servicio = Annotated[ServicioOperaciones, Depends(get_servicio)]

E400 = {"model": schemas.ErrorOut, "description": "Solicitud mal formada"}
E404 = {"model": schemas.ErrorOut, "description": "Recurso no encontrado"}
E409 = {"model": schemas.ErrorOut, "description": "Conflicto de estado o stock"}
E422 = {"model": schemas.ErrorOut, "description": "Regla de negocio violada"}


def _a_out(op) -> schemas.OperacionOut:
    return schemas.OperacionOut(
        id=op.id, actor_id=op.actor.id, estado=op.estado.value, total=op.total,
        unidades=sum(x.cantidad for x in op.lineas),
        fecha_solicitud=op.fecha_solicitud, referencia=op.referencia,
        promocion_activa=op.promocion_activa, autorizado=op.autorizado,
        motivo_cancelacion=op.motivo_cancelacion,
        lineas=[
            schemas.LineaOut(
                recurso_id=x.recurso_id, cantidad=x.cantidad,
                precio_unitario=x.precio, subtotal=x.subtotal,
            ) for x in op.lineas
        ],
        eventos=[schemas.EventoOut(nombre=e.nombre, ocurrido_en=e.ocurrido_en) for e in op.eventos],
    )


@router.get("/health", response_model=schemas.SaludOut, tags=["Sistema"])
def health(request: Request, svc: Servicio):
    ok = svc.disponible()
    return schemas.SaludOut(
        status="ok" if ok else "degradado",
        database="ok" if ok else "sin conexión",
        environment=request.app.state.settings.environment,
    )


@router.get(
    "/operaciones", response_model=schemas.ListaOperacionesOut, tags=["Operaciones"],
    summary="Consultar operaciones", responses={400: E400},
)
def listar_operaciones(
    svc: Servicio,
    estado: Annotated[str | None, Query(pattern="^(CREADO|APROBADO|SURTIDO|ENTREGADO|CANCELADO)$")] = None,
    actor_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    items, total = svc.listar(estado, actor_id, limit, offset)
    return schemas.ListaOperacionesOut(
        total=total, limit=limit, offset=offset,
        items=[
            schemas.OperacionResumen(
                id=o.id, actor_id=o.actor.id, estado=o.estado.value, total=o.total,
                unidades=sum(x.cantidad for x in o.lineas), fecha_solicitud=o.fecha_solicitud,
            ) for o in items
        ],
    )


@router.post(
    "/operaciones", response_model=schemas.OperacionOut, tags=["Operaciones"],
    status_code=status.HTTP_201_CREATED, summary="Crear operación",
    responses={400: E400, 404: E404, 422: E422},
)
def crear_operacion(datos: schemas.CrearOperacionIn, svc: Servicio):
    op = svc.crear(
        datos.actor_id, [(x.recurso_id, x.cantidad) for x in datos.lineas],
        datos.promocion_activa, datos.autorizado, datos.referencia,
    )
    return _a_out(op)


@router.get(
    "/operaciones/{operacion_id}", response_model=schemas.OperacionOut,
    tags=["Operaciones"], summary="Detalle de una operación", responses={404: E404},
)
def obtener_operacion(operacion_id: str, svc: Servicio):
    return _a_out(svc.obtener(operacion_id))


@router.get(
    "/operaciones/{operacion_id}/evaluacion", response_model=schemas.EvaluacionOut,
    tags=["Reglas"], summary="Evaluar Specifications (puede_procesarse / beneficio_referencia)",
    responses={404: E404},
)
def evaluar_operacion(operacion_id: str, svc: Servicio):
    return svc.evaluar(operacion_id)


@router.post(
    "/operaciones/{operacion_id}/aprobar", response_model=schemas.OperacionOut,
    tags=["Estados"], summary="CREADO → APROBADO",
    responses={404: E404, 409: E409, 422: E422},
)
def aprobar(operacion_id: str, svc: Servicio):
    return _a_out(svc.aprobar(operacion_id))


@router.post(
    "/operaciones/{operacion_id}/surtir", response_model=schemas.OperacionOut,
    tags=["Estados"], summary="APROBADO → SURTIDO (valida stock)",
    responses={404: E404, 409: E409, 422: E422},
)
def surtir(operacion_id: str, svc: Servicio):
    return _a_out(svc.surtir(operacion_id))


@router.post(
    "/operaciones/{operacion_id}/entregar", response_model=schemas.OperacionOut,
    tags=["Estados"], summary="SURTIDO → ENTREGADO",
    responses={404: E404, 409: E409},
)
def entregar(operacion_id: str, svc: Servicio):
    return _a_out(svc.entregar(operacion_id))


@router.post(
    "/operaciones/{operacion_id}/cancelar", response_model=schemas.OperacionOut,
    tags=["Estados"], summary="CREADO → CANCELADO",
    responses={400: E400, 404: E404, 409: E409, 422: E422},
)
def cancelar(operacion_id: str, datos: schemas.CancelarIn, svc: Servicio):
    return _a_out(svc.cancelar(operacion_id, datos.motivo))


@router.get(
    "/actores/{actor_id}/credito", response_model=schemas.CreditoOut,
    tags=["Actores"], summary="Estado de crédito del actor", responses={404: E404},
)
def credito_actor(actor_id: str, svc: Servicio):
    return svc.credito(actor_id)
