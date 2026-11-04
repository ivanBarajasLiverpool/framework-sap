---
name: e2e-test-generator
description: Flujo obligatorio paso a paso para diseñar, parametrizar y ejecutar pruebas E2E de SAP GUI utilizando robotframework-sapguilibrary, arquitectura Page Object Model (POM) pura en pages/, Pytest, reporte HTML Liverpool, toma de evidencias Base64/video y publicación a Nexus / Google Chat. Úsese siempre que se cree o modifique una transacción SAP, un Page Object o un caso de prueba.
---

# SAP GUI E2E Test Generator & POM Architecture Skill

Esta skill define las reglas obligatorias de arquitectura y el flujo de trabajo paso a paso para automatizar transacciones **SAP GUI** en este repositorio.

---

## 1. Reglas Estrictas de Arquitectura (Single Source of Truth)

1. **Prohibido usar una carpeta `modules/` o funciones sueltas de página**: Toda la lógica de interacción con pantallas de SAP vive **exclusivamente en `pages/`** bajo el patrón **Page Object Model (POM)**.
2. **Motor basado en `robotframework-sapguilibrary`**:
   - [`core/sap_engine.py`](../../core/sap_engine.py) (`SAPEngine` / `SAPDriver`) envuelve `SapGuiLibrary` junto con la captura de evidencias en Base64, resaltado de campos (`Visualize`), lectura de barra de estado y buffers (`sap.buffers`).
   - Ningún test ni Page Object debe instanciar `win32com.client` directamente ni llamar a `session.findById()` fuera de [`BasePage`](../../pages/base_page.py) o [`SAPEngine`](../../core/sap_engine.py).
3. **Separación en 4 niveles para cada transacción SAP**:
   - **Nivel 1 — Localizadores (`pages/locators/<tcode>_locators.py`)**: Solo constantes `str` o listas de IDs técnicos de SAP GUI (`wnd[0]/usr/...`) y rutas de menú. Prohibido incluir lógica aquí.
   - **Nivel 2 — Clase Base (`pages/modules/base_page.py`)**: Contiene los verbos genéricos reutilizables que delegan en `SapGuiLibrary` y registran evidencias automáticamente.
   - **Nivel 3 — Page Object de Transacción (`pages/modules/<tcode>_page.py`)**: Hereda de `BasePage`, importa sus localizadores desde `pages/locators/` y expone métodos de negocio claros y encadenables (`return self`).
   - **Nivel 4 — Caso de Prueba (`tests/test_<tcode>_<flujo>.py`)**: Solo instancia las clases Page Object (o recibe sus fixtures de `conftest.py`), invoca métodos de negocio y ejecuta `assert`.
4. **Respeto absoluto al flujo de Evidencias, Reportes y Nexus**:
   - No modificar ni deshabilitar los hooks de [`conftest.py`](../../conftest.py) (`pytest_runtest_makereport`, `pytest_html_results_summary`, `pytest_unconfigure`).
   - Todo nuevo caso de prueba debe registrarse en [`data/expected_result.csv`](../../data/expected_result.csv) para que aparezca en la cortinilla de video (`show_intro`) y en el recuadro de Resultado Esperado del reporte HTML Liverpool enviado a **Nexus**.

---

## 2. Estructura Oficial del Proyecto

```text
sap_automation_framework/
├── .env                            # Credenciales SAP, banderas visuales y URLs/Keys de Nexus y Google Chat
├── conftest.py                     # Fixtures (sap, fb01_page, fb03_page) y hooks hacia Reporte/Nexus
├── config/
│   └── settings.py                 # Lectura centralizada de variables de entorno (Config)
├── core/
│   ├── sap_engine.py               # Wrapper sobre SapGuiLibrary + Capturas Base64 + Buffers + Subscreens
│   ├── sap_driver.py               # Alias SAPDriver -> SAPEngine
│   └── sheet_runner.py             # Ejecutor opcional Data-Driven por matriz Excel/CSV
├── pages/                          # ÚNICA CAPA DE PAGE OBJECT MODEL (POM)
│   ├── __init__.py                 # Exporta BasePage, LoginPage, páginas de transacciones y locators
│   ├── modules/                    # Clases Page Object por transacción
│   │   ├── __init__.py
│   │   ├── base_page.py            # Superclase POM con verbos de SapGuiLibrary y toma de evidencias
│   │   ├── login_page.py           # POM de login SAP + resolución de logon múltiple
│   │   ├── fb01_page.py            # POM de transacción FB01
│   │   └── fb03_page.py            # POM de transacción FB03
│   └── locators/                   # Selectores puros desacoplados por transacción
│       ├── __init__.py
│       ├── common_locators.py      # OKCode, Toolbar estándar, Statusbar, Login
│       ├── fb01_locators.py
│       └── fb03_locators.py
├── data/
│   └── expected_result.csv         # Mapeo test_id -> resultado_esperado para cortinilla y HTML
├── tests/
│   └── test_<tcode>_<feature>.py   # Suites de pruebas Pytest consumiendo exclusivamente pages/
└── utils/
    ├── report_template.py          # Inyección de plantilla HTML Liverpool y línea de tiempo Base64
    ├── visual.py                   # Cortinilla Tkinter (show_intro) y grabación MP4 (ffmpeg)
    ├── notifier.py                 # Upload de HTML y MP4 a Nexus + Tarjeta CardV2 en Google Chat
    └── logger.py
```

---

## 3. Catálogo de Métodos Disponibles en `BasePage`

Al crear cualquier `<TCode>Page(BasePage)`, utiliza siempre los métodos heredados de [`BasePage`](../../pages/base_page.py) para garantizar que cada acción use `SapGuiLibrary`, resalte el control en rojo y capture la evidencia paso a paso:

### Navegación y Ventanas
- `self.abrir_transaccion(tcode: str)` → Ejecuta `/n<tcode>` mediante `SapGuiLibrary.run_transaction`.
- `self.presionar_enter(descripcion: str = "Enter")` → Envía `VKey 0` (`SapGuiLibrary.send_vkey`).
- `self.guardar(descripcion: str = "Clic en Guardar / Contabilizar")` → Presiona `wnd[0]/tbar[0]/btn[11]`.
- `self.enviar_vkey(vkey: int | str, ventana: str = "wnd[0]", descripcion: str = None)` → Envía teclas virtuales (`0`=Enter, `3`=Back/F3, `8`=F8, `11`=Ctrl+S, `12`=Cancelar/ESC).
- `self.seleccionar_menu(ruta_menu: str)` → Navega por textos visibles separados por `->` (ej. `"Documento->Visualizar"`).
- `self.seleccionar_menu_por_id(menu_id: str, etiqueta: str = None)` → Selecciona un `GuiMenu` por su ID.
- `self.maximizar_ventana(ventana: int | str = 0)` → Maximiza la ventana SAP.
- `self.obtener_titulo_ventana(ventana: str = "wnd[0]") -> str` → Retorna el título de la ventana.

### Interacción con Controles de Formulario
- `self.escribir(locator: str, valor: str, etiqueta: str)` → `SapGuiLibrary.input_text` + evidencia.
- `self.escribir_password(locator: str, password: str, etiqueta: str = "Contraseña")` → `SapGuiLibrary.input_password` (enmascara `********` en logs y reporte).
- `self.escribir_en_id_dinamico(posibles_locators: List[str], valor: str, etiqueta: str) -> str` → Intenta escribir en la lista de IDs o busca recursivamente el campo por sufijo cuando el número de `subBLOCK` cambia dinámicamente.
- `self.clic(locator: str, etiqueta: str)` → `SapGuiLibrary.click_element` (botones, pestañas `GuiTab`, menús).
- `self.marcar_checkbox(locator: str, seleccionado: bool = True, etiqueta: str = None)` → `select_checkbox` / `unselect_checkbox`.
- `self.seleccionar_radio_button(locator: str, etiqueta: str = None)` → `select_radio_button`.
- `self.seleccionar_combo(locator: str, valor: str, etiqueta: str = None)` → `select_from_list_by_label`.
- `self.obtener_valor(locator: str) -> str` → `SapGuiLibrary.get_value`.

### Tablas y GridViews (ALV)
- `self.obtener_valor_celda(tabla_locator: str, fila: int, columna_id: str) -> str` → `get_cell_value`.
- `self.escribir_en_celda(tabla_locator: str, fila: int, columna_id: str, valor: str, etiqueta: str = None)` → `set_cell_value`.
- `self.seleccionar_fila_tabla(tabla_locator: str, fila: int, etiqueta: str = None)` → `select_table_row`.
- `self.contar_filas_tabla(tabla_locator: str) -> int` → `get_row_count`.
- `self.clic_boton_tabla(tabla_locator: str, boton_id: str, etiqueta: str = None)` → `click_toolbar_button`.

### Validaciones, Barra de Estado, Buffers y Evidencias
- `self.verificar_elemento_presente(locator: str, mensaje: str = None)` → `element_should_be_present`.
- `self.verificar_valor_elemento(locator: str, valor_esperado: str, mensaje: str = None)` → `element_value_should_be`.
- `self.verificar_elemento_contiene(locator: str, texto_esperado: str, mensaje: str = None)` → `element_value_should_contain`.
- `self.obtener_info_barra_estado() -> Dict[str, str]` → Retorna `{"text", "type", "id", "number", "parameter_1"}`.
- `self.capturar_documento_de_barra_estado(buffer_name: str = "NumDocContable", expected_text_contains: str = "se contabilizó") -> str` → Verifica el mensaje en `wnd[0]/sbar`, guarda el número de documento en `sap.buffers[buffer_name]` y lo retorna.
- `self.guardar_buffer(nombre: str, valor: str)` / `self.obtener_buffer(nombre: str) -> str`.
- `self.tomar_evidencia(nombre_paso: str) -> str` → Guarda una captura PNG adicional en `reports/`.

---

## 4. Flujo Paso a Paso para Crear una Nueva Automatización

### Paso 1: Definir los Localizadores en `pages/locators/<tcode>_locators.py`
Extrae los IDs de SAP GUI (a partir de `wnd[0]/...` o `wnd[1]/...`) y agrúpalos en una clase de constantes:

```python
# pages/locators/fb50_locators.py
class FB50Locators:
    """IDs de controles SAP GUI para la transacción FB50."""

    TCODE = "FB50"
    TXT_FECHA_DOCUMENTO = "wnd[0]/usr/subHEADER:SAPLFSKB:0100/ctxtINVFO-BLDAT"
    TXT_FECHA_CONTAB = "wnd[0]/usr/subHEADER:SAPLFSKB:0100/ctxtINVFO-BUDAT"
    TXT_REFERENCIA = "wnd[0]/usr/subHEADER:SAPLFSKB:0100/txtINVFO-XBLNR"
    GRID_POSICIONES = "wnd[0]/usr/subITEMS:SAPLFSKB:0100/tblSAPLFSKBTABLE"
```
Exporta la clase en [`pages/locators/__init__.py`](../../pages/locators/__init__.py).

---

### Paso 2: Crear el Page Object en `pages/modules/<tcode>_page.py`
Crea la clase de página heredando de `BasePage`:

```python
# pages/modules/fb50_page.py
from pages.modules.base_page import BasePage
from pages.locators.fb50_locators import FB50Locators


class FB50Page(BasePage):
    """Page Object de la transacción FB50."""

    def abrir(self) -> "FB50Page":
        self.abrir_transaccion(FB50Locators.TCODE)
        return self

    def completar_cabecera(self, fecha_doc: str, fecha_contab: str, referencia: str) -> "FB50Page":
        self.escribir(FB50Locators.TXT_FECHA_DOCUMENTO, fecha_doc, "Fecha documento")
        self.escribir(FB50Locators.TXT_FECHA_CONTAB, fecha_contab, "Fecha contabilización")
        self.escribir(FB50Locators.TXT_REFERENCIA, referencia, "Referencia")
        self.presionar_enter("Validar cabecera FB50")
        return self

    def contabilizar_y_obtener_documento(self, buffer_name: str = "NumDocFB50") -> str:
        self.guardar("Contabilizar documento FB50")
        return self.capturar_documento_de_barra_estado(
            buffer_name=buffer_name,
            expected_text_contains="se contabilizó",
        )
```
Exporta la nueva página en [`pages/__init__.py`](../../pages/__init__.py) y, si es de uso frecuente, agrega su fixture en [`conftest.py`](../../conftest.py).

---

### Paso 3: Registrar el Resultado Esperado en `data/expected_result.csv`
Agrega el identificador del caso (ej. `FB50_001`) en [`data/expected_result.csv`](../../data/expected_result.csv):

```csv
test_id,resultado_esperado
FB01_001,El documento contable se contabiliza exitosamente en FB01 generando un número de documento en la barra de estado y mostrándose en FB03.
FB50_001,La póliza de cuenta de mayor se registra en FB50 sin errores y devuelve el número de documento contable en la barra de estado.
```

---

### Paso 4: Crear el Test Declarativo en `tests/test_<tcode>_<flujo>.py`
El nombre de la función de prueba **debe incluir el `test_id`** (ej. `test_FB50_001_...`) para que `report_template.py` enlace automáticamente su resultado esperado:

```python
# tests/test_fb50_contabilizacion.py
from pages.modules.fb50_page import FB50Page
from pages.modules.fb03_page import FB03Page


def test_FB50_001_contabilizacion_cuenta_mayor(sap):
    """
    TC_FB50_001: Contabilización directa de cuenta de mayor en FB50 y validación en FB03.
    """
    fb50 = FB50Page(sap)
    fb03 = FB03Page(sap)

    fb50.abrir()
    fb50.completar_cabecera(
        fecha_doc="14.10.2026",
        fecha_contab="14.10.2026",
        referencia="REF-001",
    )

    num_doc = fb50.contabilizar_y_obtener_documento(buffer_name="NumDocContable")
    assert num_doc, "No se obtuvo número de documento tras contabilizar en FB50."

    resultado = fb03.validar_documentos_financieros(min_documentos=1, buffer_name="NumDocContable")
    assert resultado["num_doc_contabilizado"] == num_doc
```

---

## 5. Comandos de Ejecución y Verificación

1. **Verificar sintaxis y recolección de Pytest (sin tocar SAP):**
   ```powershell
   python -m pytest --collect-only
   ```
2. **Ejecutar un test generando el Reporte HTML Liverpool, Video y enviando a Nexus / Google Chat:**
   ```powershell
   pytest tests/test_fb01_contabilizacion.py --html=reports/report.html --self-contained-html -v -s
   ```
3. **Ejecutar en modo desarrollo rápido (solo consola, sin subir a Nexus):**
   ```powershell
   pytest tests/test_fb01_contabilizacion.py -v -s
   ```
