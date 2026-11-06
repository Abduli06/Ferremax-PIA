"""Genera docs/api/openapi.json (entregable de la carpeta docs/api/)."""
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("DATABASE_URL", f"sqlite:///{tempfile.gettempdir()}/ferremax_openapi.db")

from src.api.main import app  # noqa: E402

destino = Path("docs/api/openapi.json")
destino.parent.mkdir(parents=True, exist_ok=True)
destino.write_text(json.dumps(app.openapi(), indent=2, ensure_ascii=False), encoding="utf-8")
print(f"OpenAPI exportado en {destino}")
