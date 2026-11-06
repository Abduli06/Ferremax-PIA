from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum

MONTO_BENEFICIO = Decimal("1500")


class DomainException(Exception):
    status_code = 422


class DatosInvalidos(DomainException):
    status_code = 422


class ReglaNegocioViolada(DomainException):
    status_code = 422


class TransicionInvalida(DomainException):
    status_code = 409


class StockInsuficiente(DomainException):
    status_code = 409


class OperacionNoEncontrada(DomainException):
    status_code = 404


class ActorNoEncontrado(DomainException):
    status_code = 404


@dataclass(frozen=True)
class Actor:
    id: str
    nombre: str
    es_preferente: bool
    activo: bool
    ciudad: str


@dataclass(frozen=True)
class Recurso:
    id: str
    descripcion: str
    precio: Decimal
    stock: int
    habilitado: bool


@dataclass(frozen=True)
class Linea:
    recurso_id: str
    cantidad: int
    precio: Decimal

    def __post_init__(self):
        if self.cantidad <= 0:
            raise DatosInvalidos("La cantidad debe ser mayor a 0")

    @property
    def subtotal(self) -> Decimal:
        return self.precio * self.cantidad


class Estado(StrEnum):
    CREADO = "CREADO"
    APROBADO = "APROBADO"
    SURTIDO = "SURTIDO"
    ENTREGADO = "ENTREGADO"
    CANCELADO = "CANCELADO"


TRANSICIONES = {
    Estado.CREADO: {Estado.APROBADO, Estado.CANCELADO},
    Estado.APROBADO: {Estado.SURTIDO},
    Estado.SURTIDO: {Estado.ENTREGADO},
    Estado.ENTREGADO: set(),
    Estado.CANCELADO: set(),
}


@dataclass(frozen=True)
class EventoDominio:
    nombre: str
    operacion_id: str
    ocurrido_en: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )



class Specification:
    def is_satisfied_by(self, op: "Operacion") -> bool:
        raise NotImplementedError

    def __and__(self, otra):
        return _Fn(lambda o: self.is_satisfied_by(o) and otra.is_satisfied_by(o))

    def __or__(self, otra):
        return _Fn(lambda o: self.is_satisfied_by(o) or otra.is_satisfied_by(o))

    def __invert__(self):
        return _Fn(lambda o: not self.is_satisfied_by(o))


class _Fn(Specification):
    def __init__(self, fn):
        self.fn = fn

    def is_satisfied_by(self, op):
        return self.fn(op)


class ActorActivoSpec(Specification):
    def is_satisfied_by(self, op):
        return op.actor.activo


class DetalleNoVacioSpec(Specification):
    def is_satisfied_by(self, op):
        return len(op.lineas) > 0


class AutorizadaSpec(Specification):
    def is_satisfied_by(self, op):
        return op.autorizado


class ActorPreferenteSpec(Specification):
    def is_satisfied_by(self, op):
        return op.actor.es_preferente


class MontoMinimoSpec(Specification):
    def __init__(self, minimo: Decimal):
        self.minimo = minimo

    def is_satisfied_by(self, op):
        return op.total >= self.minimo


class PromocionActivaSpec(Specification):
    def is_satisfied_by(self, op):
        return op.promocion_activa


puede_procesarse = ActorActivoSpec() & DetalleNoVacioSpec() & AutorizadaSpec()
beneficio_referencia = (
    ActorPreferenteSpec() & MontoMinimoSpec(MONTO_BENEFICIO) & ~PromocionActivaSpec()
)


@dataclass
class Operacion:
    id: str
    actor: Actor
    referencia: str
    fecha_solicitud: str
    promocion_activa: bool = False
    autorizado: bool = True
    lineas: list = field(default_factory=list)
    estado: Estado = Estado.CREADO
    motivo_cancelacion: str | None = None
    eventos: list = field(default_factory=list)

    @property
    def total(self) -> Decimal:
        return sum((x.subtotal for x in self.lineas), Decimal("0"))

    def motivos_no_procesable(self) -> list[str]:
        motivos = []
        if not ActorActivoSpec().is_satisfied_by(self):
            motivos.append("El actor está inactivo")
        if not DetalleNoVacioSpec().is_satisfied_by(self):
            motivos.append("La operación no tiene líneas")
        if not AutorizadaSpec().is_satisfied_by(self):
            motivos.append("La operación no está autorizada")
        return motivos

    def _transicionar(self, destino: Estado, evento: str):
        if destino not in TRANSICIONES[self.estado]:
            raise TransicionInvalida(
                f"No se puede pasar de {self.estado.value} a {destino.value}"
            )
        self.estado = destino
        self.eventos.append(EventoDominio(evento, self.id))

    def aprobar(self):
        if Estado.APROBADO not in TRANSICIONES[self.estado]:
            raise TransicionInvalida(
                f"No se puede aprobar una operación en estado {self.estado.value}"
            )
        if not puede_procesarse.is_satisfied_by(self):
            raise ReglaNegocioViolada("; ".join(self.motivos_no_procesable()))
        self._transicionar(Estado.APROBADO, "OperacionAprobada")

    def surtir(self, catalogo: dict):
        if Estado.SURTIDO not in TRANSICIONES[self.estado]:
            raise TransicionInvalida(
                f"No se puede surtir una operación en estado {self.estado.value}"
            )
        for linea in self.lineas:
            recurso = catalogo.get(linea.recurso_id)
            if recurso is None or not recurso.habilitado:
                raise ReglaNegocioViolada(
                    f"El recurso {linea.recurso_id} no está habilitado"
                )
            if linea.cantidad > recurso.stock:
                raise StockInsuficiente(
                    f"Stock insuficiente de {linea.recurso_id}: "
                    f"pide {linea.cantidad}, hay {recurso.stock}"
                )
        self._transicionar(Estado.SURTIDO, "OperacionSurtida")

    def entregar(self):
        if Estado.ENTREGADO not in TRANSICIONES[self.estado]:
            raise TransicionInvalida(
                f"No se puede entregar una operación en estado {self.estado.value}"
            )
        self._transicionar(Estado.ENTREGADO, "OperacionEntregada")

    def cancelar(self, motivo: str):
        if Estado.CANCELADO not in TRANSICIONES[self.estado]:
            raise TransicionInvalida(
                f"Solo se cancela una operación CREADA (estado actual: {self.estado.value})"
            )
        if not motivo or not motivo.strip():
            raise DatosInvalidos("Falta el motivo de cancelación")
        self.motivo_cancelacion = motivo.strip()
        self._transicionar(Estado.CANCELADO, "OperacionCancelada")

    def a_dict(self) -> dict:
        return {
            "id": self.id,
            "actor_id": self.actor.id,
            "referencia": self.referencia,
            "fecha_solicitud": self.fecha_solicitud,
            "promocion_activa": self.promocion_activa,
            "autorizado": self.autorizado,
            "lineas": [
                {"recurso_id": x.recurso_id, "cantidad": x.cantidad, "precio": str(x.precio)}
                for x in self.lineas
            ],
            "estado": self.estado.value,
            "motivo_cancelacion": self.motivo_cancelacion,
            "eventos": [
                {"nombre": e.nombre, "operacion_id": e.operacion_id, "ocurrido_en": e.ocurrido_en}
                for e in self.eventos
            ],
        }

    @classmethod
    def desde_dict(cls, d: dict, actores: dict) -> "Operacion":
        return cls(
            id=d["id"],
            actor=actores[d["actor_id"]],
            referencia=d["referencia"],
            fecha_solicitud=d["fecha_solicitud"],
            promocion_activa=d["promocion_activa"],
            autorizado=d["autorizado"],
            lineas=[
                Linea(x["recurso_id"], x["cantidad"], Decimal(x["precio"]))
                for x in d["lineas"]
            ],
            estado=Estado(d["estado"]),
            motivo_cancelacion=d["motivo_cancelacion"],
            eventos=[EventoDominio(**e) for e in d["eventos"]],
        )
