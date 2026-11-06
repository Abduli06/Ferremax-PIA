import csv
import threading
from datetime import date
from decimal import Decimal
from pathlib import Path

from src.api.dominio_temporal import (
    Actor,
    ActorNoEncontrado,
    DatosInvalidos,
    Estado,
    Linea,
    Operacion,
    OperacionNoEncontrada,
    Recurso,
    beneficio_referencia,
    puede_procesarse,
)
from src.api.persistencia_temporal import RepositorioSnapshots


def _filas(ruta: Path) -> list[dict]:
    with ruta.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def cargar_csv(data_dir: Path):
    actores = {
        r["actor_id"]: Actor(
            r["actor_id"], r["nombre"], bool(int(r["es_preferente"])),
            bool(int(r["activo"])), r["ciudad"],
        )
        for r in _filas(data_dir / "actores.csv")
    }
    catalogo = {
        r["recurso_id"]: Recurso(
            r["recurso_id"], r["descripcion"], Decimal(r["precio_mxn"]),
            int(r["capacidad_o_stock"]), bool(int(r["habilitado"])),
        )
        for r in _filas(data_dir / "catalogo.csv")
    }
    operaciones = {
        r["operacion_id"]: Operacion(
            id=r["operacion_id"],
            actor=actores[r["actor_id"]],
            referencia=r["referencia"],
            fecha_solicitud=r["fecha_solicitud"],
            promocion_activa=bool(int(r["promocion_activa"])),
            autorizado=bool(int(r["autorizado"])),
            estado=Estado(r["estado_inicial"]),
        )
        for r in _filas(data_dir / "operaciones.csv")
    }
    for r in _filas(data_dir / "detalle_operaciones.csv"):
        recurso = catalogo[r["recurso_id"]]
        operaciones[r["operacion_id"]].lineas.append(
            Linea(recurso.id, int(r["cantidad"]), recurso.precio)
        )
    return actores, catalogo, operaciones


class ServicioOperaciones:
    def __init__(self, data_dir: Path, repo: RepositorioSnapshots):
        self._repo = repo
        self._data_dir = data_dir
        self._lock = threading.RLock()
        self.actores, self.catalogo, self._ops = cargar_csv(data_dir)
        for snap in repo.cargar_todo():  
            self._ops[snap["id"]] = Operacion.desde_dict(snap, self.actores)

 
    def listar(self, estado=None, actor_id=None, limit=50, offset=0):
        with self._lock:
            ops = sorted(self._ops.values(), key=lambda o: o.id)
            if estado:
                ops = [o for o in ops if o.estado.value == estado]
            if actor_id:
                ops = [o for o in ops if o.actor.id == actor_id]
            return ops[offset: offset + limit], len(ops)

    def obtener(self, operacion_id: str) -> Operacion:
        with self._lock:
            op = self._ops.get(operacion_id)
        if op is None:
            raise OperacionNoEncontrada(f"Operación {operacion_id} no encontrada")
        return op

    def evaluar(self, operacion_id: str) -> dict:
        op = self.obtener(operacion_id)
        return {
            "operacion_id": op.id,
            "puede_procesarse": puede_procesarse.is_satisfied_by(op),
            "motivos": op.motivos_no_procesable(),
            "beneficio_referencia": beneficio_referencia.is_satisfied_by(op),
            "total": op.total,
        }

    def credito(self, actor_id: str) -> dict:
        actor = self.actores.get(actor_id)
        if actor is None:
            raise ActorNoEncontrado(f"Actor {actor_id} no encontrado")
        with self._lock:
            propias = [o for o in self._ops.values() if o.actor.id == actor_id]
        abiertas = [o for o in propias if o.estado in (Estado.CREADO, Estado.APROBADO, Estado.SURTIDO)]
        return {
            "actor_id": actor.id,
            "activo": actor.activo,
            "es_preferente": actor.es_preferente,
            "credito_suspendido": not actor.activo,
            "operaciones_abiertas": len(abiertas),
            "monto_abierto": sum((o.total for o in abiertas), Decimal("0")),
        }


    def crear(self, actor_id, lineas, promocion_activa=False, autorizado=True, referencia=None):
        actor = self.actores.get(actor_id)
        if actor is None:
            raise ActorNoEncontrado(f"Actor {actor_id} no encontrado")
        nuevas = []
        for recurso_id, cantidad in lineas:
            recurso = self.catalogo.get(recurso_id)
            if recurso is None:
                raise DatosInvalidos(f"El recurso {recurso_id} no existe en el catálogo")
            nuevas.append(Linea(recurso.id, cantidad, recurso.precio))
        with self._lock:
            siguiente = max((int(i.split("O")[-1]) for i in self._ops), default=0) + 1
            nuevo_id = f"FER-O{siguiente:03d}"
            op = Operacion(
                id=nuevo_id, actor=actor,
                referencia=referencia or f"API_{nuevo_id}",
                fecha_solicitud=date.today().isoformat(),
                promocion_activa=promocion_activa,
                autorizado=autorizado, lineas=nuevas,
            )
            self._ops[nuevo_id] = op
            self._repo.guardar(op.a_dict())
        return op

    def _mutar(self, operacion_id: str, accion):
        with self._lock:
            op = self.obtener(operacion_id)
            accion(op)  
            self._repo.guardar(op.a_dict())
            return op

    def aprobar(self, operacion_id):
        return self._mutar(operacion_id, lambda o: o.aprobar())

    def surtir(self, operacion_id):
        return self._mutar(operacion_id, lambda o: o.surtir(self.catalogo))

    def entregar(self, operacion_id):
        return self._mutar(operacion_id, lambda o: o.entregar())

    def cancelar(self, operacion_id, motivo):
        return self._mutar(operacion_id, lambda o: o.cancelar(motivo))

    def reiniciar(self):
        """Solo para pruebas/demo: vuelve a la semilla de los CSV."""
        with self._lock:
            self._repo.vaciar()
            _, _, self._ops = cargar_csv(self._data_dir)

    def disponible(self) -> bool:
        return self._repo.disponible()
