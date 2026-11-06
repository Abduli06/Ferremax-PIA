API de FerreMax: cómo ejecutarla y desplegarla

Esta guía explica cómo correr la API en nuestra computadora, con Docker y en la nube (Render).

1. Ejecutar sin Docker

Pasos en la terminal, dentro de la carpeta del proyecto:

bash
python -m venv .venv
.venv\Scripts\Activate.ps1        # en Windows
source .venv/bin/activate         # en Linux o Mac
pip install -r requirements-dev.txt

Copiamos el archivo de variables de entorno:

bash
copy .env.example .env            # en Windows
cp .env.example .env              # en Linux o Mac

Levantamos la API y abrimos Swagger en http://127.0.0.1:8000/docs:

bash
uvicorn src.api.main:app --reload

Para correr las pruebas (piden mínimo 80% de cobertura) y el revisor de estilo:

bash
pytest
ruff check src tests
2. Ejecutar con Docker Compose

Docker Compose levanta tres cosas: la base de datos (PostgreSQL), la API y las pruebas.

Copiar .env.example a .env y cambiar POSTGRES_PASSWORD por una clave sencilla (solo letras y números).
Levantar la API:
bash
docker compose up --build

La API queda en http://localhost:8000/docs.

Correr las pruebas contra PostgreSQL (usan la base ferremax_test):
bash
docker compose --profile tests run --rm tests

Si marca que la base ferremax_test no existe, hay que borrar el volumen y volver a levantar:

bash
docker compose down -v
3. Despliegue en Render
Subir el proyecto a GitHub e iniciar sesión en render.com con la cuenta de GitHub.
Dar clic en New + y luego en Blueprint. Elegir el repositorio.
Render lee el archivo render.yaml y crea la API (con Docker) y una base de datos PostgreSQL.
Esperar a que el estado sea Live. La documentación queda en https://<nuestro-servicio>.onrender.com/docs.
Cada vez que se hace push a main, Render vuelve a desplegar solo.

Notas:

Si no queremos base de datos, se borran del render.yaml la variable DATABASE_URL y el bloque databases. En ese caso la API usa SQLite y los datos se pierden en cada despliegue.
El plan gratuito apaga el servicio después de 15 minutos sin uso, así que conviene abrir /docs un minuto antes de la demostración.
La base de datos gratuita de Render dura 30 días.
4. Pruebas en Swagger

En /docs se abre cada endpoint, se da clic en Try it out y luego en Execute. Con los datos de los CSV, estas peticiones dan cada código:

Código	Petición	Qué pasa
200	POST /operaciones/FER-O001/aprobar	La operación pasa a APROBADO
200	GET /operaciones/FER-O001	Regresa la operación con sus líneas y eventos
201	POST /operaciones con {"actor_id":"FER-C001","lineas":[{"recurso_id":"FER-P001","cantidad":2}]}	Se crea la operación
400	GET /operaciones?estado=VOLANDO	El estado no existe, la solicitud está mal hecha
404	GET /operaciones/FER-O999	La operación no existe
409	Repetir POST /operaciones/FER-O001/aprobar	La transición ya no es válida
409	POST /operaciones/FER-O002/surtir sin haberla aprobado	No se puede saltar de estado
422	POST /operaciones/FER-O027/aprobar	El cliente está inactivo
422	POST /operaciones/FER-O008/aprobar	La operación no está autorizada

Las operaciones cambian de estado y se guardan en la base de datos. Si se repite la prueba hay que usar otra operación o reiniciar la base.

5. Códigos de error
Código	Significado
400	Solicitud mal formada
404	No se encontró el recurso
409	Conflicto con el estado o con el stock
422	Se violó una regla de negocio

Las respuestas de error tienen esta forma:

json
{"detail": "mensaje del error", "codigo": "NombreDeLaExcepcion"}
6. Pendiente: conectar con el dominio real

Por ahora la API usa los archivos src/api/dominio_temporal.py y src/api/persistencia_temporal.py. Cuando estén listos src/domain y src/application:

En src/api/servicio.py se cambian los imports para llamar a los casos de uso reales.
Las excepciones del dominio deben indicar su código HTTP (409, 422 o 404), o se adaptan en src/api/errores.py.
Se borran los archivos *_temporal.py y se corre pytest.
7. Limitaciones
GET /actores/{id}/credito: los CSV no traen línea de crédito, así que solo indica si el actor está activo y cuántas operaciones tiene abiertas.
surtir revisa que haya stock y que el artículo esté habilitado, pero no descuenta el stock del catálogo.