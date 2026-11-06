from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ErrorOut(BaseModel):
    detail: str
    codigo: str | None = Field(None, description="Nombre de la excepción de dominio")


class LineaIn(BaseModel):
    recurso_id: str = Field(..., examples=["FER-P001"])
    cantidad: int = Field(..., gt=0, examples=[2])


class CrearOperacionIn(BaseModel):
    actor_id: str = Field(..., examples=["FER-C001"])
    lineas: list[LineaIn] = Field(default_factory=list)
    promocion_activa: bool = False
    autorizado: bool = True
    referencia: str | None = None


class CancelarIn(BaseModel):
    motivo: str = Field(..., examples=["El cliente ya no requiere el pedido"])


class LineaOut(BaseModel):
    recurso_id: str
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal


class EventoOut(BaseModel):
    nombre: str
    ocurrido_en: datetime | str


class OperacionResumen(BaseModel):
    id: str
    actor_id: str
    estado: str
    total: Decimal
    unidades: int
    fecha_solicitud: str


class OperacionOut(OperacionResumen):
    model_config = ConfigDict(json_schema_extra={"example": {
        "id": "FER-O001", "actor_id": "FER-C025", "estado": "CREADO",
        "total": "5150.00", "unidades": 7, "fecha_solicitud": "2026-10-02",
        "referencia": "PIA_FER_001", "promocion_activa": False, "autorizado": True,
        "motivo_cancelacion": None, "lineas": [], "eventos": [],
    }})
    referencia: str
    promocion_activa: bool
    autorizado: bool
    motivo_cancelacion: str | None
    lineas: list[LineaOut]
    eventos: list[EventoOut]


class ListaOperacionesOut(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[OperacionResumen]


class EvaluacionOut(BaseModel):
    operacion_id: str
    puede_procesarse: bool
    motivos: list[str]
    beneficio_referencia: bool
    total: Decimal


class CreditoOut(BaseModel):
    actor_id: str
    activo: bool
    es_preferente: bool
    credito_suspendido: bool
    operaciones_abiertas: int
    monto_abierto: Decimal


class SaludOut(BaseModel):
    status: str
    database: str
    environment: str
