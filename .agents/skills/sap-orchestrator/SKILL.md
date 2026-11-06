---
name: sap-orchestrator
description: "Skill del Agente Orquestador Multiagente para automatización SAP GUI. Actívala siempre que el usuario pida automatizar un flujo desde un archivo .md en test_cases/, ejecutar el pipeline multiagente o coordinar a los subagentes (flow-interpreter, sap-scraper, pom-test-builder, env-data-manager y qa-evaluator)."
---

# Agente Orquestador de Automatización SAP GUI (`sap-orchestrator`)

Cuando se active esta skill, **tú (el Agente Principal de Antigravity) actúas como el Agente Orquestador**. Tu responsabilidad es coordinar secuencialmente a los **5 subagentes especialistas** del repositorio para transformar un documento funcional en `test_cases/*.md` en una prueba automatizada SAP GUI completa, parametrizada en `.env` y validada en ejecución.

---

## Catálogo de Subagentes Especialistas

Las especificaciones completas de cada subagente residen en [`.agents/agents/`](../../agents/):

| Orden | Nombre del Subagente | Archivo de Definición | Permisos de Escritura | Misión Principal |
| :---: | :--- | :--- | :---: | :--- |
| **1** | `flow-interpreter` | [`.agents/agents/flow-interpreter.md`](../../agents/flow-interpreter.md) | `false` (Solo lectura) | Lee el `.md` en `test_cases/` y genera el **Contrato Técnico Estructurado**. |
| **2** | `sap-scraper` | [`.agents/agents/sap-scraper.md`](../../agents/sap-scraper.md) | `true` | Ejecuta [`sap_gui_scraper.py`](./scripts/sap_gui_scraper.py) en SAP GUI y construye `pages/locators/<tcode>_locators.py`. |
| **3** | `pom-test-builder` | [`.agents/agents/pom-test-builder.md`](../../agents/pom-test-builder.md) | `true` | Crea `pages/modules/<tcode>_page.py`, `tests/test_<tcode>_<flujo>.py` y actualiza `data/expected_result.csv`. |
| **4** | `env-data-manager` | [`.agents/agents/env-data-manager.md`](../../agents/env-data-manager.md) | `true` | Extrae insumos a `.env`, los expone en `config/settings.py` (`Config`) y los inyecta en `tests/`. |
| **5** | `qa-evaluator` | [`.agents/agents/qa-evaluator.md`](../../agents/qa-evaluator.md) | `true` (Ejecuta Pytest) | Audita la arquitectura POM, verifica el consumo de `Config` y ejecuta el test con `pytest`. |

---

## Protocolo de Orquestación Paso a Paso

Sigue estrictamente este flujo de control utilizando las herramientas nativas `define_subagent` (si un subagente aún no está registrado en la sesión actual) e `invoke_subagent`:

### Paso 0: Registro de Subagentes en la Sesión (si aplica)
Si los subagentes de `.agents/agents/*.md` no aparecen aún en tu lista de subagentes disponibles en el turno actual, lee su archivo `.agents/agents/<nombre>.md` y regístralos usando `define_subagent` con su `Name`, `Description`, `SystemPrompt` y permisos correspondientes (`EnableWriteTools`).

### Fase 1 — Interpretación del Flujo (`flow-interpreter`)
1. Invoca al subagente `flow-interpreter` con `invoke_subagent` indicándole la ruta del archivo en `test_cases/<archivo>.md`.
2. Espera su respuesta con el **Contrato Técnico del Caso de Prueba** (`test_id`, `T-Codes`, secuencia de pantallas, insumos candidatos para `.env` y resultado esperado).

### Fase 2 — Scraping de Localizadores en SAP (`sap-scraper`)
1. Pasa el Contrato Técnico al subagente `sap-scraper` mediante `invoke_subagent`.
2. `sap-scraper` utilizará [`.agents/skills/sap-orchestrator/scripts/sap_gui_scraper.py`](./scripts/sap_gui_scraper.py) para inspeccionar SAP GUI pantalla por pantalla y generar/actualizar `pages/locators/<tcode>_locators.py`.
3. Recibe el mapa de constantes de localizadores creados.

### Fase 3 — Construcción POM y Caso de Prueba (`pom-test-builder`)
1. Invoca a `pom-test-builder` entregándole el Contrato Técnico de la Fase 1 y el mapa de localizadores de la Fase 2.
2. `pom-test-builder` creará/actualizará:
   - `pages/modules/<tcode>_page.py` (heredando de `BasePage`)
   - `tests/test_<tcode>_<flujo>.py` (con sus validaciones y `assert`)
   - `data/expected_result.csv`

### Fase 4 — Parametrización de Insumos en `.env` (`env-data-manager`)
1. Invoca a `env-data-manager` indicándole el archivo de prueba generado y la tabla de insumos del Contrato Técnico.
2. `env-data-manager` registrará las variables en `.env`, las expondrá en `config/settings.py` (`Config`) y actualizará `tests/test_<tcode>_<flujo>.py` para consumirlas mediante `Config.<VARIABLE>`.

### Fase 5 — Evaluación y Ejecución QA (`qa-evaluator`)
1. Invoca a `qa-evaluator` para que audite los archivos generados y ejecute `pytest`.
2. **Bucle de Retroalimentación (Self-Healing)**:
   - Si `qa-evaluator` reporta `RECHAZADO ❌`, identifica en su dictamen cuál subagente (`sap-scraper`, `pom-test-builder` o `env-data-manager`) debe corregir el hallazgo, envíale un mensaje con `send_message` (o re-invócalo) y vuelve a pasar por `qa-evaluator` hasta obtener `APROBADO ✅`.
3. Presenta al usuario el resumen ejecutivo final con enlaces a todos los archivos creados/modificados y el resultado de la prueba.

