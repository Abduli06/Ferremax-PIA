import json
from datetime import UTC, datetime

from sqlalchemy import DateTime, String, Text, create_engine, delete, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    pass


class OperacionRow(Base):
    __tablename__ = "operaciones_snapshot"

    operacion_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    estado: Mapped[str] = mapped_column(String(16))
    snapshot: Mapped[str] = mapped_column(Text)
    actualizado: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class RepositorioSnapshots:
    def __init__(self, database_url: str):
        kwargs = {}
        if database_url.startswith("sqlite"):
            kwargs["connect_args"] = {"check_same_thread": False}
        self.engine = create_engine(database_url, pool_pre_ping=True, **kwargs)
        Base.metadata.create_all(self.engine)

    def cargar_todo(self) -> list[dict]:
        with Session(self.engine) as s:
            return [json.loads(r.snapshot) for r in s.scalars(select(OperacionRow))]

    def guardar(self, datos: dict) -> None:
        with Session(self.engine) as s, s.begin():
            fila = s.get(OperacionRow, datos["id"])
            if fila is None:
                fila = OperacionRow(operacion_id=datos["id"])
                s.add(fila)
            fila.estado = datos["estado"]
            fila.snapshot = json.dumps(datos, ensure_ascii=False)
            fila.actualizado = datetime.now(UTC)

    def vaciar(self) -> None:
        with Session(self.engine) as s, s.begin():
            s.execute(delete(OperacionRow))

    def disponible(self) -> bool:
        try:
            with self.engine.connect() as c:
                c.exec_driver_sql("SELECT 1")
            return True
        except Exception:
            return False
