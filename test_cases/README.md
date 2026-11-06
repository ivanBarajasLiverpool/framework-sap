# Catálogo de Casos de Prueba en Markdown (`test_cases/`)

Este directorio almacena las especificaciones funcionales de casos de prueba en formato Markdown (`.md`) que sirven como **insumo de entrada** para el **Sistema Multiagente de Automatización SAP** en Antigravity.

## Flujo de Consumo por los Agentes

1. **`flow-interpreter` (Subagente 1)**: Lee el archivo `.md` de este directorio y extrae el `test_id`, las transacciones (`T-Codes`), los pasos secuenciales por pantalla, los insumos de datos y las validaciones esperadas.
2. **`sap-scraper` (Subagente 2)**: Navega en SAP GUI siguiendo los pasos del `.md` y extrae los localizadores técnicos reales (`wnd[0]/usr/...`) hacia `pages/locators/`.
3. **`pom-test-builder` (Subagente 3)**: Construye el Page Object (`pages/modules/`), el script de prueba (`tests/`) y registra el resultado esperado en `data/expected_result.csv`.
4. **`env-data-manager` (Subagente 4)**: Parametriza los insumos del caso en `.env` y `config/settings.py` (`Config`).
5. **`qa-evaluator` (Subagente 5)**: Ejecuta el caso de prueba con `pytest` y audita que la arquitectura y las validaciones sean óptimas.

## Cómo agregar un nuevo caso

1. Copia el archivo [`TEMPLATE_CASO_PRUEBA.md`](./TEMPLATE_CASO_PRUEBA.md) con el nombre `TC_<TCODE>_<NUM>_<flujo>.md` (ejemplo: `TC_FB50_001_registro_poliza.md`).
2. Completa las secciones de metadatos, pasos e insumos.
3. Pídele a Antigravity en el chat:
   > *"Orquesta la automatización del flujo `test_cases/TC_FB50_001_registro_poliza.md`"*

