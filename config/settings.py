import os
from dotenv import load_dotenv

# Mismo patrón que infra-it-automation-pao: permite apuntar a otro archivo con ENV_FILE
_env_file = os.getenv("ENV_FILE")
if _env_file and os.path.exists(_env_file):
    load_dotenv(_env_file, override=True)
else:
    load_dotenv(override=True)


def _bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in ("true", "1", "yes", "si", "sí")


class Config:
    # ── Conexión SAP ──────────────────────────────────────────────
    # "attach" = usa la sesión de SAP GUI ya abierta | "login" = abre SAP Logon y hace login con .env
    SAP_MODE = os.getenv("SAP_MODE", "attach").lower()
    SAP_LOGON_PATH = os.getenv("SAP_LOGON_PATH", r"C:\Program Files (x86)\SAP\FrontEnd\SAPgui\saplogon.exe")
    SAP_SYSTEM = os.getenv("SAP_SYSTEM")            # Nombre exacto de la entrada en SAP Logon
    SAP_CLIENT = os.getenv("SAP_CLIENT")            # Mandante
    SAP_USER = os.getenv("SAP_USER")
    SAP_PASS = os.getenv("SAP_PASS")
    SAP_LANGUAGE = os.getenv("SAP_LANGUAGE", "ES")
    SAP_CONNECTION_INDEX = int(os.getenv("SAP_CONNECTION_INDEX", 0))
    SAP_SESSION_INDEX = int(os.getenv("SAP_SESSION_INDEX", 0))

    # ── Validaciones visuales ─────────────────────────────────────
    HEADLESS = _bool("HEADLESS", "false")                    # En SAP GUI: si es false, maximiza y trae SAP al frente
    HIGHLIGHT_FIELDS = _bool("HIGHLIGHT_FIELDS", "true")     # Marco rojo SAP (Visualize) en cada campo
    STEP_SCREENSHOTS = _bool("STEP_SCREENSHOTS", "false")    # false = solo captura final/fallo; true = en cada paso
    SHOW_INTRO = _bool("SHOW_INTRO", "true")                 # Cortinilla con nombre del test / resultado esperado
    INTRO_SECONDS = float(os.getenv("INTRO_SECONDS", 3))
    RECORD_VIDEO = _bool("RECORD_VIDEO", "false")            # Requiere ffmpeg en PATH
    FFMPEG_PATH = os.getenv("FFMPEG_PATH", "ffmpeg")

    # ── Reporte / Nexus / Google Chat ─────────────────────────────
    PROJECT_NAME = os.getenv("PROJECT_NAME", "SAP ECC → S/4HANA")
    NEXUS_PROJECT = os.getenv("NEXUS_PROJECT", "SAP_S4H")
    NEXUS_BASE_URL = os.getenv("NEXUS_BASE_URL", "https://nexushub.up.railway.app").rstrip("/")
    NEXUS_API_KEY = os.getenv("NEXUS_API_KEY")
    SKIP_NEXUS_UPLOAD = _bool("SKIP_NEXUS_UPLOAD", "false")
    GOOGLE_CHAT_WEBHOOK = os.getenv("AUTO_ACC")              # Mismo nombre de variable que el framework PAO
    GOOGLE_CHAT_SUBTITLE = os.getenv("GOOGLE_CHAT_SUBTITLE", "SAP Migración ECC to S4H")

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    REPORTS_DIR = os.path.join(BASE_DIR, "reports")
    REPORT_PATH = os.path.join(REPORTS_DIR, "report.html")
