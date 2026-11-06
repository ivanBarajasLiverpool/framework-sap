# Reglas del Proyecto y Sistema Multiagente SAP GUI (`framework-sap`)

Este repositorio implementa un framework de automatización E2E para **SAP GUI** sobre `robotframework-sapguilibrary`, Pytest, Page Object Model (POM) de 4 capas y un **Sistema Multiagente para Antigravity**.

---

## 1. Arquitectura de 4 Capas (Invariante Obligatoria)

1. **Capa 1 — Localizadores (`pages/locators/<tcode>_locators.py`)**: Únicamente constantes con IDs relativos de SAP GUI (`wnd[0]/usr/...`). Prohibido incluir lógica.
2. **Capa 2 — Superclase Base ([`pages/modules/base_page.py`](pages/modules/base_page.py))**: Envuelve [`SAPEngine`](core/sap_engine.py) y `SapGuiLibrary` registrando evidencias Base64 y resaltado en rojo (`Visualize`).
3. **Capa 3 — Page Objects (`pages/modules/<tcode>_page.py`)**: Heredan de `BasePage` y exponen acciones de negocio encadenables (`return self`).
4. **Capa 4 — Casos de Prueba (`tests/test_<tcode>_<flujo>.py`)**: Funciones `def test_<TEST_ID>_...(sap):` que consumen los Page Objects, leen sus insumos desde [`Config`](config/settings.py) (alimentado por `.env`) y validan con `assert`. Todo `<TEST_ID>` debe estar registrado en [`data/expected_result.csv`](data/expected_result.csv).

---

## 2. Sistema Multiagente y Directorio `test_cases/`

- Todas las especificaciones funcionales de casos de prueba en Markdown viven en el directorio [`test_cases/`](test_cases/).
- Cuando el usuario solicite crear, automatizar o actualizar un caso de prueba a partir de un archivo `.md` en `test_cases/` (o pida ejecutar el flujo multiagente), **activa obligatoriamente la skill [`sap-orchestrator`](.agents/skills/sap-orchestrator/SKILL.md)** y actúa como **Agente Orquestador** delegando el trabajo en orden a los 5 subagentes definidos en [`.agents/agents/`](.agents/agents/):
  1. **`flow-interpreter`** ([`.agents/agents/flow-interpreter.md`](.agents/agents/flow-interpreter.md)): Interpreta el flujo desde `test_cases/<archivo>.md`.
  2. **`sap-scraper`** ([`.agents/agents/sap-scraper.md`](.agents/agents/sap-scraper.md)): Va a SAP GUI con [`sap_gui_scraper.py`](.agents/skills/sap-orchestrator/scripts/sap_gui_scraper.py) y extrae los localizadores hacia `pages/locators/`.
  3. **`pom-test-builder`** ([`.agents/agents/pom-test-builder.md`](.agents/agents/pom-test-builder.md)): Construye el Page Object en `pages/modules/`, el test en `tests/` con sus validaciones y actualiza `data/expected_result.csv`.
  4. **`env-data-manager`** ([`.agents/agents/env-data-manager.md`](.agents/agents/env-data-manager.md)): Identifica insumos, los prepara en `.env` + `config/settings.py` (`Config`) y los consume desde `tests/`.
  5. **`qa-evaluator`** ([`.agents/agents/qa-evaluator.md`](.agents/agents/qa-evaluator.md)): Ejecuta el caso de prueba con `pytest` y evalúa que la lógica y estructura de los demás agentes sea óptima.

