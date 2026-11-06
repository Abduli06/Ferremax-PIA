#️ FerreMax — Sistema de Gestión Comercial e Inventarios (PIA)

> **Producto Integrador de Aprendizaje (PIA)**  
> **Universidad Autónoma de Nuevo León** | **Facultad de Ingeniería Mecánica y Eléctrica (FIME)**  
> **Unidad de Aprendizaje:** Componentes de Lógica de Negocios  
> **Grupo:** 003 M6 | **Equipo:** 17  
> **Caso de Estudio:** FerreMax (Ferretería y Venta Empresarial)

---

## Integrantes del Equipo

| Nombre | Matrícula | Rol Asignado |
| :--- | :---: | :--- |
| **Cristian Alelí García Ávalos** | 2226880 | Integrante 1 — Líder de Dominio, TDD, Reglas de Negocio y Seguridad |
| **Juan Manuel Casanova Ávila** | 2269091 | Integrante 2 — Líder de Persistencia, Mocks Externos y Pipeline CI/CD |
| **Abdul Alí Vázquez Flores** | 2227013 | Integrante 3 — Líder de Calidad, Cobertura, Aplicación PIA, Reporte y GitHub |
---

## Enlaces Principales de Evaluación

* **Despliegue Funcional en la Nube (Swagger UI / OpenAPI):** [https://ferremax-api.onrender.com/docs](https://ferremax-api.onrender.com/docs)
---

## Descripción del Proyecto

**FerreMax** es una solución empresarial orientada al dominio (**Domain-Driven Design - DDD**) diseñada para solventar problemáticas críticas de negocio en la comercialización de materiales de plomería, electricidad y construcción a través de tres sucursales y un almacén central.

El sistema erradica de forma determinista la venta accidental de mercancía comprometida o en tránsito (BR001, BR013), automatiza la reserva de inventario en tiempo real, vigila las líneas de crédito empresarial suspendiendo transacciones ante saldos vencidos (BR007, BR008) y gestiona con precisión la vigencia y excepciones de cotizaciones comerciales (BR004, BR005).

---

## Características Principales

* **Núcleo DDD Puro:** Modelado de entidades ricas, Value Objects inmutables (`Money` implementado con precisión fija mediante `Decimal`, `PoliticaVigencia`, `PoliticaDescuento`), Aggregate Roots (`Order`, `Customer`, `CatalogItem`) y emisión de *Domain Events* (`StockMinimoAlcanzadoEvent`, `CreditoSuspendidoEvent`).
* **Specification Pattern:** Reglas de validación y descuentos desacopladas y combinables mediante sobrecarga de operadores booleanos (`&` AND, `|` OR, `~` NOT).
* **Máquina de Estados Finita:** Control estricto de transiciones de ciclo de vida (`CREADO` $\rightarrow$ `APROBADO` $\rightarrow$ `SURTIDO` $\rightarrow$ `ENTREGADO` / `CANCELADO`), impidiendo estados inconsistentes o dobles confirmaciones.
* **Dataset Integrado (17_FerreMax):** Ingesta, orquestación y validación automatizada sobre 40 actores, 20 artículos de catálogo, 60 operaciones transaccionales, 120 casos de prueba y 20 transiciones de estado.
* **Arquitectura Hexagonal & Layered:** Aislamiento total de las reglas de negocio respecto a los mecanismos de entrega (FastAPI REST) y persistencia (SQLAlchemy con patrón Repository y Unit of Work).

---

## Estructura del Repositorio

```text
FerreMax-PIA/
├── .github/
│   └── workflows/
│       └── ci.yml                 # Pipeline automatizado de CI/CD (GitHub Actions)
├── docs/
│   ├── BRD.md                     # Requerimientos de negocio, 20 User Stories (Gherkin), BPMN y Glosario
│   ├── architecture/              # Mapa de Dominio DDD, Diagramas UML, Revisión SOLID y 3 ADRs
│   └── api/                       # Especificación OpenAPI / Swagger (openapi.json)
├── datos/
│   ├── actores.csv                # 40 compradores y clientes empresariales de FerreMax
│   ├── catalogo.csv               # 20 artículos ferreteros con SKU, precios y stock mínimo
│   ├── operaciones.csv            # 60 operaciones base registradas
│   ├── detalle_operaciones.csv    # Partidas y renglones de las operaciones
│   ├── casos_prueba.csv           # 120 casos de prueba automatizados
│   └── transiciones_prueba.csv    # 20 transiciones de estado a evaluar
├── src/
│   ├── domain/                    # Entidades, Value Objects, Agregados, Eventos y Specifications
│   ├── application/               # Servicios de aplicación, Commands, Queries (CQRS) y Handlers
│   ├── infrastructure/            # Cargador de CSV, repositorios SQLAlchemy y Unit of Work
│   └── api/                       # Controladores REST HTTP construidos con FastAPI
├── tests/
│   ├── test_domain.py             # Pruebas unitarias de invariantes, TDD y reglas de negocio
│   ├── test_repository.py         # Pruebas de integración relacional con SQLite (commit / rollback)
│   ├── test_service.py            # Simulación de pasarelas y servicios externos con unittest.mock
│   ├── test_security.py           # Matriz de autorización y políticas de cancelación
│   └── test_pia_cases.py          # Runner automatizado de los 120 casos y 20 transiciones
├── .env.example                   # Plantilla de variables de configuración (12-Factor App)
├── .gitignore                     # Exclusión de entornos virtuales (.venv/) y cachés
├── docker-compose.yml             # Orquestación de contenedores (App + DB + Tests)
├── Dockerfile                     # Construcción de la imagen contenerizada
├── pyproject.toml                 # Configuración de pytest, cobertura y linter Ruff
├── requirements.txt               # Dependencias fijadas del proyecto
└── README.md                      # Documentación central del repositorio
```

---

## Trazabilidad Arquitectural

El sistema mantiene correspondencia bidireccional directa entre las definiciones de las etapas de análisis y la implementación de software:

* **ADR-001:** Adopción del patrón *Domain Model* frente a *Transaction Script* para salvaguardar invariantes complejas de inventario y crédito.

* **ADR-002:** Desacoplamiento de almacenamiento mediante *Repository Pattern* y garantía de atomicidad transaccional con *Unit of Work*.

* **ADR-003:** Segregación de operaciones de lectura y escritura (*CQRS básico*) para optimizar consultas de inventario multi-sucursal sin comprometer el modelo transaccional.

## Ejecución de la API 
- Local: ver docs/api/DESPLIEGUE.md sección 1
- Docker: cp .env.example .env && docker compose up --build  → http://localhost:8000/docs
- Pruebas: pytest
- Producción (Render): https://ferremax-api.onrender.com/docs
