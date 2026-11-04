"""
Integraciones remotas, replicadas de infra-it-automation-pao/conftest.py (pytest_unconfigure):
  1. Subida del reporte HTML a Nexus  -> POST {NEXUS_BASE_URL}/api/reports/upload  (header X-API-Key)
  2. Subida del video de evidencia    -> POST {NEXUS_BASE_URL}/api/videos/upload
  3. Tarjeta CardV2 en Google Chat     -> POST webhook (variable AUTO_ACC)
"""
import os
from datetime import datetime

import requests
import urllib3

from config.settings import Config
from utils.logger import get_logger

logger = get_logger("Notifier")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ICON_OK = "https://upload.wikimedia.org/wikipedia/commons/thumb/7/73/Flat_tick_icon.svg/120px-Flat_tick_icon.svg.png"
ICON_FAIL = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8f/Flat_cross_icon.svg/120px-Flat_cross_icon.svg.png"
ICON_INFO = "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e4/Infobox_info_icon.svg/120px-Infobox_info_icon.svg.png"


def _nexus_headers():
    return {"X-API-Key": Config.NEXUS_API_KEY} if Config.NEXUS_API_KEY else {}


def upload_report_to_nexus(html_path: str):
    """Sube el HTML a Nexus. Devuelve la URL pública del reporte o None."""
    if not html_path or not os.path.exists(html_path):
        return None
    try:
        logger.info(f"[*] Subiendo reporte HTML a Nexus: {html_path}")
        nombre_reporte = os.path.basename(html_path)
        try:
            with open(html_path, "r", encoding="utf-8") as f:
                contenido_html = f.read()
        except UnicodeDecodeError:
            with open(html_path, "r", encoding="cp1252", errors="replace") as f:
                contenido_html = f.read()

        r = requests.post(
            f"{Config.NEXUS_BASE_URL}/api/reports/upload",
            files={"file": (nombre_reporte, contenido_html.encode("utf-8"), "text/html")},
            headers=_nexus_headers(),
            verify=False,
            timeout=30,
        )
        if r.status_code == 201:
            filename = r.json().get("filename", nombre_reporte)
            url = f"{Config.NEXUS_BASE_URL}/reports/{filename}"
            logger.info(f"[*] Reporte subido con éxito: {url}")
            return url
        logger.error(f"[-] Error al subir reporte: {r.status_code} - {r.text}")
    except Exception as e:
        logger.error(f"[-] Excepción al subir reporte HTML: {e}")
    return None


def upload_latest_video_to_nexus(videos_dir: str):
    """Sube el video más reciente de reports/videos a Nexus. Devuelve URL o None."""
    if not os.path.isdir(videos_dir):
        return None
    videos = [os.path.join(videos_dir, f) for f in os.listdir(videos_dir) if f.lower().endswith((".webm", ".mp4"))]
    if not videos:
        return None
    latest = max(videos, key=os.path.getmtime)
    try:
        logger.info(f"[*] Subiendo video de evidencia a Nexus: {latest}")
        with open(latest, "rb") as f:
            r = requests.post(
                f"{Config.NEXUS_BASE_URL}/api/videos/upload",
                files={"file": (os.path.basename(latest), f)},
                headers=_nexus_headers(),
                verify=False,
                timeout=60,
            )
        if r.status_code == 201:
            filename = r.json().get("filename", os.path.basename(latest))
            url = f"{Config.NEXUS_BASE_URL}/reports/{filename}"
            logger.info(f"[*] Video subido con éxito: {url}")
            return url
        logger.error(f"[-] Error al subir video: {r.status_code} - {r.text}")
    except Exception as e:
        logger.error(f"[-] Excepción al subir video: {e}")
    return None


def send_google_chat_card(passed: int, failed: int, report_url: str = None, video_url: str = None):
    """Envía la tarjeta CardV2 de resumen al webhook de Google Chat (AUTO_ACC)."""
    webhook_url = Config.GOOGLE_CHAT_WEBHOOK
    if not webhook_url:
        logger.warning("[!] Webhook URL (AUTO_ACC) no encontrada en .env. No se enviará notificación.")
        return False

    fecha_str = datetime.now().strftime("El %Y-%m-%d a las %H:%M hrs")
    buttons = [{"text": "Ver reportes", "onClick": {"openLink": {"url": f"{Config.NEXUS_BASE_URL}/"}}}]
    if report_url:
        buttons.append({"text": "Ver este reporte", "onClick": {"openLink": {"url": report_url}}})
    if video_url:
        buttons.append({"text": "Ver video", "onClick": {"openLink": {"url": video_url}}})

    widgets = [
        {"decoratedText": {"startIcon": {"iconUrl": ICON_OK}, "text": f"Exitosos: {passed}"}},
        {"decoratedText": {"startIcon": {"iconUrl": ICON_FAIL}, "text": f"Fallidos: {failed}"}},
        {"decoratedText": {"startIcon": {"knownIcon": "CLOCK"}, "text": f"Fecha: {fecha_str}"}},
        {"decoratedText": {"startIcon": {"iconUrl": ICON_INFO},
                           "text": "Nota: Es necesario ingresar al reporte de histórico de Nexus para ver el reporte",
                           "wrapText": True}},
    ]
    if video_url:
        widgets.append({"decoratedText": {"startIcon": {"knownIcon": "VIDEO_CAMERA"},
                                          "text": "Evidencia de video: Expira y se elimina en 24 hrs.",
                                          "wrapText": True}})
    widgets.append({"buttonList": {"buttons": buttons}})

    payload = {
        "cardsV2": [{
            "cardId": "sap_test_execution_report",
            "card": {
                "header": {
                    "title": "AUTOMATIZACIÓN DE PRUEBAS SAP",
                    "subtitle": Config.GOOGLE_CHAT_SUBTITLE,
                    "imageUrl": ICON_FAIL if failed > 0 else ICON_OK,
                    "imageType": "CIRCLE",
                },
                "sections": [{"header": "Resumen de ejecución", "widgets": widgets}],
            },
        }]
    }

    try:
        r = requests.post(webhook_url, json=payload,
                          headers={"Content-Type": "application/json; charset=UTF-8"}, timeout=10)
        logger.info(f"[*] Notificación de Google Chat enviada. Status Code: {r.status_code}")
        return r.status_code == 200
    except Exception as e:
        logger.error(f"[-] Error al enviar notificación a Google Chat: {e}")
        return False


def publish_results(html_path: str, passed: int, failed: int):
    """Flujo completo post-ejecución: Nexus (reporte + video) -> Google Chat."""
    if Config.SKIP_NEXUS_UPLOAD:
        logger.info("[!] Subida a Nexus y notificación omitidas por SKIP_NEXUS_UPLOAD.")
        return
    if passed + failed == 0:
        logger.warning("[!] No se ejecutaron pruebas. No se enviará notificación.")
        return
    report_url = upload_report_to_nexus(html_path)
    video_url = upload_latest_video_to_nexus(os.path.join(os.path.dirname(html_path), "videos"))
    send_google_chat_card(passed, failed, report_url, video_url)
