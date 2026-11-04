# Framework de Automatización SAP GUI en Python (`SapGuiLibrary` + POM + Reportes Nexus)

Este framework en Python utiliza **`robotframework-sapguilibrary` (`SapGuiLibrary`)** bajo una arquitectura **Page Object Model (POM)** ejecutada con **`pytest`**, conservando íntegramente:
- **Reporte HTML interactivo Liverpool** (`templates/mock_report.html` + `utils/report_template.py`).
- **Toma de evidencias paso a paso** en Base64 con resaltado de controles (`Visualize`) y grabación de video (`ffmpeg`).
- **Publicación automática a Nexus y notificación a Google Chat** (`utils/notifier.py`).
- **Ejecución Data-Driven** desde Excel / CSV (`core/sheet_runner.py`).

## Estructura del Proyecto

```text
sap_automation_framework/
├── requirements.txt
├── README.md
├── conftest.py                     # Fixtures (sap, fb01_page, fb03_page) y hooks de reporte/Nexus
├── config/
│   └── settings.py                 # Variables de entorno (.env) y banderas visuales
├── core/
│   ├── sap_engine.py               # Wrapper sobre SapGuiLibrary + Evidencias Base64 + Buffers
│   ├── sap_driver.py               # Alias semántico SAPDriver -> SAPEngine
│   └── sheet_runner.py             # Ejecutor Data-Driven desde Excel/CSV
├── pages/                          # Arquitectura Page Object Model (POM)
│   ├── __init__.py
│   ├── base_page.py                # Clase base con verbos SAPGuiLibrary, barras de estado y evidencias
│   ├── login_page.py               # POM para autenticación en SAP Logon
│   ├── fb01_page.py                # POM para Contabilización de Documentos (FB01)
│   ├── fb03_page.py                # POM para Visualización y Validación de Documentos (FB03)
│   └── locators/                   # Selectores desacoplados por transacción
│       ├── __init__.py
│       ├── common_locators.py
│       ├── fb01_locators.py
│       └── fb03_locators.py
├── utils/
│   ├── logger.py
│   ├── notifier.py                 # Subida de HTML/Video a Nexus y tarjeta en Google Chat
│   ├── report_template.py          # Inyección de plantilla Liverpool en pytest-html
│   └── visual.py                   # Cortinilla Tkinter y grabación de video con ffmpeg
├── data/
│   ├── expected_result.csv         # Resultados esperados por caso de prueba
│   └── matriz_fb01.csv             # Matriz de pasos para sheet_runner
├── tests/
│   └── test_fb01_contabilizacion.py
└── reports/                        # Reportes HTML, capturas y videos de ejecución
```

## Instalación y Uso Rápido

1. **Instalar dependencias:**
   ```powershell
   pip install -r requirements.txt
   ```
2. **Configurar `.env`** (`SAP_MODE=attach` o `SAP_MODE=login`) y tener **SAP GUI Scripting** habilitado.
3. **Ejecutar las pruebas POM con Pytest y generar reporte para Nexus:**
   ```powershell
   pytest tests/test_fb01_contabilizacion.py --html=reports/report.html --self-contained-html -v -s
   ```
4. **Ejecutar directamente leyendo la matriz de Sheets/CSV:**
   ```powershell
   python -m core.sheet_runner data/matriz_fb01.csv
   ```

## Documentación Detallada
Consulta la **[Guía Completa del Framework (`GUIA_FRAMEWORK_SAP.md`)](GUIA_FRAMEWORK_SAP.md)** para conocer:
- División detallada de la arquitectura y responsabilidades por capa.
- Cómo inicializar un proyecto desde cero y habilitar SAP GUI Scripting.
- Cómo configurar conexiones (`attach` vs `login`) e identificar selectores técnicos en SAP GUI.
- Tutorial paso a paso para crear nuevos Page Objects, casos de prueba y publicar evidencias a Nexus.
