import os
import sys
from datetime import datetime

import pytest

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from config.settings import Config  # noqa: E402  (carga el .env)
from utils.logger import get_logger  # noqa: E402
from utils.report_template import (  # noqa: E402
    add_test_result, generate_html_summary, clear_results, get_expected_result, _CURRENT_STEPS, _ELITE_CASES,
)
from utils.visual import show_intro, VideoRecorder  # noqa: E402
from utils.notifier import publish_results  # noqa: E402

logger = get_logger("Conftest")


# ──────────────────────────────────────────────────────────────
# FIXTURES
# ──────────────────────────────────────────────────────────────
@pytest.fixture(autouse=True)
def clear_steps_before_test():
    _CURRENT_STEPS.clear()
    yield


@pytest.fixture(scope="session")
def _video_session(request):
    """Graba el escritorio durante toda la suite SOLO si se genera reporte HTML y RECORD_VIDEO=true."""
    html_path = request.config.getoption("htmlpath", default=None)
    recorder = VideoRecorder(os.path.join(os.path.dirname(html_path or Config.REPORT_PATH), "videos"))
    if html_path:
        recorder.start()
    yield recorder
    recorder.stop()


@pytest.fixture(scope="function")
def sap(request, _video_session):
    """
    Fixture por test:
    1. Muestra cortinilla de presentación (nombre del test y resultado esperado).
    2. Abre conexión a SAP y realiza login automático usando los datos del archivo .env.
    3. Entrega la instancia de SAPEngine al test.
    4. Teardown: Cierra la sesión de SAP (/nex) al terminar el test para dejar el entorno limpio.
    """
    from core.sap_engine import SAPEngine

    show_intro(request.node.name, get_expected_result(request.node.name))
    logger.info(f"[*] [SETUP TEST] Iniciando sesión SAP para '{request.node.name}' (modo: {Config.SAP_MODE})...")

    # Inicia sesión usando from_config() que lee SAP_SYSTEM, SAP_CLIENT, SAP_USER, SAP_PASS
    engine = SAPEngine.from_config()
    engine.buffers.clear()

    yield engine

    # Teardown: Cerrar sesión después del test
    logger.info(f"[*] [TEARDOWN TEST] Cerrando sesión de SAP para '{request.node.name}'...")
    try:
        engine.close_session()
    except Exception as e:
        logger.warning(f"[-] No se pudo cerrar la sesión de SAP limpiamente: {e}")


@pytest.fixture(scope="function")
def fb01_page(sap):
    """Fixture POM que entrega una instancia lista de `FB01Page` conectada a la sesión activa."""
    from pages.modules.fb01_page import FB01Page
    return FB01Page(sap)


@pytest.fixture(scope="function")
def fb03_page(sap):
    """Fixture POM que entrega una instancia lista de `FB03Page` conectada a la sesión activa."""
    from pages.modules.fb03_page import FB03Page
    return FB03Page(sap)


# ──────────────────────────────────────────────────────────────
# HOOKS DE REPORTE (mismo flujo que infra-it-automation-pao)
# ──────────────────────────────────────────────────────────────
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    pytest_html = item.config.pluginmanager.getplugin("html")
    outcome = yield
    report = outcome.get_result()
    extra = getattr(report, "extras", [])

    screenshot_b64 = add_test_result(item, report, item.funcargs.get("sap"))
    if screenshot_b64 and pytest_html:
        extra.append(pytest_html.extras.image(screenshot_b64, "Evidencia de Ejecución"))
    report.extras = extra


def pytest_configure(config):
    htmlpath = config.getoption("htmlpath", default=None)
    if htmlpath:
        dir_name = os.path.dirname(htmlpath) or "reports"
        os.makedirs(dir_name, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        _, ext = os.path.splitext(os.path.basename(htmlpath))
        config.option.htmlpath = os.path.join(dir_name, f"report_{timestamp}{ext}")


def pytest_html_report_title(report):
    report.title = f"Reporte de Automatización SAP - Liverpool"


def pytest_html_results_summary(prefix, summary, postfix):
    generate_html_summary(prefix, None)


def pytest_sessionstart(session):
    clear_results()


def pytest_unconfigure(config):
    """Al terminar: sube reporte/video a Nexus y envía tarjeta a Google Chat."""
    html_path = getattr(config.option, "htmlpath", None)
    if not html_path:
        logger.info("[!] No se generó reporte HTML. Se omite Nexus / Google Chat.")
        return
    passed = sum(1 for c in _ELITE_CASES if c["outcome"] == "passed")
    failed = sum(1 for c in _ELITE_CASES if c["outcome"] in ["failed", "error"])
    publish_results(html_path, passed, failed)
