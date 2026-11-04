import os
import re
import csv
import json
import base64
from datetime import datetime

from config.settings import Config
from utils.logger import get_logger

logger = get_logger("TemplateReport")

# Estado global de la ejecución (mismo modelo que templete_report.py de PAO)
_ELITE_CASES = []
_CURRENT_STEPS = []
_SESSION_INFO = {"system": "SAP", "client": "", "user": ""}


def set_session_info(system: str = "", client: str = "", user: str = ""):
    _SESSION_INFO.update({"system": system or "SAP", "client": client or "", "user": user or ""})


def get_base64_logos():
    logo_path = os.path.join(Config.BASE_DIR, "assets", "Logo")
    logos = {"liverpool": "", "coe": ""}
    try:
        for key, name in (("liverpool", "Logoliver.png"), ("coe", "centro_excelencia.png")):
            path = os.path.join(logo_path, name)
            if os.path.exists(path):
                with open(path, "rb") as f:
                    logos[key] = base64.b64encode(f.read()).decode()
    except Exception as e:
        logger.error(f"Error cargando logos en base64: {e}")
    return logos


def add_step(message, status="passed", screenshot_b64=None):
    """Registra un paso en la línea de tiempo del test (opcionalmente con captura de SAP)."""
    _CURRENT_STEPS.append({
        "message": message,
        "status": status,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "screenshot_b64": screenshot_b64,
    })
    logger.info(f"STEP: {message}")


def clear_results():
    _ELITE_CASES.clear()
    _CURRENT_STEPS.clear()


def get_expected_result(test_name: str):
    """
    Busca el resultado esperado en data/expected_result.csv (columnas: test_id,resultado_esperado).
    Coincide si test_id está contenido en el nombre del test (ej. 'FB01_001' en test_FB01_001_...).
    """
    csv_path = os.path.join(Config.BASE_DIR, "data", "expected_result.csv")
    if not os.path.exists(csv_path):
        return None
    try:
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            next(reader, None)
            for fila in reader:
                if len(fila) >= 2 and fila[0].strip() and fila[0].strip().lower() in test_name.lower():
                    return fila[1].strip()
    except Exception as e:
        logger.warning(f"[-] No se pudo leer expected_result.csv: {e}")
    return None


def add_test_result(item, report, sap):
    """Se invoca desde pytest_runtest_makereport. Guarda resultado, pasos y captura final."""
    screenshot_b64 = None
    if report.when != "call":
        return None

    if sap is not None:
        try:
            screenshot_b64 = sap.screenshot_base64()
        except Exception as e:
            logger.error(f"Error capturando pantalla final de SAP: {e}")

    log_content = ""
    if report.failed:
        log_content = report.longreprtext
        match = re.search(r"(?:AssertionError|LookupError|RuntimeError):\s*(.*)", log_content)
        if match:
            log_content = match.group(1).strip()

    steps = list(_CURRENT_STEPS)
    if not any(s["message"] == "Inicio" for s in steps):
        steps.insert(0, {"message": "Inicio", "status": "passed",
                         "timestamp": datetime.now().strftime("%H:%M:%S"), "screenshot_b64": None})

    outcome_label = "Finalizado" if report.passed else "Error Detectado"
    steps.append({"message": outcome_label, "status": report.outcome,
                  "timestamp": datetime.now().strftime("%H:%M:%S"), "screenshot_b64": None})

    _ELITE_CASES.append({
        "nodeid": report.nodeid,
        "test_name": item.name,
        "outcome": report.outcome,
        "duration": report.duration,
        "screenshot_b64": screenshot_b64,
        "log": log_content,
        "steps": steps,
        "expected_result": get_expected_result(item.name),
    })
    _CURRENT_STEPS.clear()
    return screenshot_b64


def generate_html_summary(prefix, config=None):
    """Inyecta la plantilla Liverpool (templates/mock_report.html) dentro del reporte de pytest-html."""
    template_path = os.path.join(Config.BASE_DIR, "templates", "mock_report.html")
    try:
        with open(template_path, "r", encoding="utf-8-sig") as template_file:
            mock_html = template_file.read()
    except Exception as e:
        logger.error(f"No se pudo leer la plantilla mock_report.html: {e}")
        return

    logos = get_base64_logos()
    session_date = datetime.now().strftime("%Y-%m-%d")
    sap_label = f"SAP {_SESSION_INFO['system']}" + (f" / Mandante {_SESSION_INFO['client']}" if _SESSION_INFO["client"] else "")

    passed = sum(1 for c in _ELITE_CASES if c["outcome"] == "passed")
    failed = sum(1 for c in _ELITE_CASES if c["outcome"] in ["failed", "error"])
    total = passed + failed
    total_duration = sum(c["duration"] for c in _ELITE_CASES)
    percent = int(round((passed / total) * 100)) if total > 0 else 0
    dash_offset = 440 - (440 * percent / 100)
    duration_text = f"{total_duration:.1f}s" if total_duration >= 1 else f"{total_duration:.2f}s"

    elite_data_json = json.dumps(_ELITE_CASES).replace("</", "<\\/")

    mock_html = (
        mock_html
        .replace("[[NEXUS_PROJECT]]", Config.NEXUS_PROJECT)
        .replace('src="Logo/Logoliver.png"', f'src="data:image/png;base64,{logos["liverpool"]}"')
        .replace('src="Logo/centro_excelencia.png"', f'src="data:image/png;base64,{logos["coe"]}"')
        .replace("Sesión: 2026-03-25 • Chrome 122\r\n                        • QA", f"Sesión: {session_date} • {sap_label} • QA")
        .replace("Sesión: 2026-03-25 • Chrome 122\n                        • QA", f"Sesión: {session_date} • {sap_label} • QA")
        .replace('<span class="value">0 / 0</span>', f'<span class="value">{passed} / {total}</span>', 1)
        .replace('<span class="value">0 / 0</span>', f'<span class="value">{failed} / {total}</span>', 1)
        .replace('<span class="value">0s</span>', f'<span class="value">{duration_text}</span>')
        .replace('<div class="donut-text">0%', f'<div class="donut-text">{percent}%')
        .replace('<circle class="donut-fill" cx="75" cy="75" r="70"></circle>',
                 f'<circle class="donut-fill" cx="75" cy="75" r="70" style="stroke-dasharray: 440; stroke-dashoffset: {dash_offset};"></circle>')
    )

    style_match = re.search(r"<style>(.*?)</style>", mock_html, flags=re.DOTALL)
    script_match = re.search(r"<script>(.*?)</script>", mock_html, flags=re.DOTALL)
    container_match = re.search(r'(<div class="container">.*?</div>\s*)<script>', mock_html, flags=re.DOTALL)

    if not (style_match and script_match and container_match):
        logger.error("No se pudo extraer CSS/HTML/script desde mock_report.html.")
        return

    injected = (
        f'<meta name="nexus-project" content="{Config.NEXUS_PROJECT}">\n'
        f"<style>{style_match.group(1)}</style>\n"
        f'<div class="elite-overlay">{container_match.group(1)}</div>\n'
        f"<script>{script_match.group(1)}</script>\n"
        f"{_get_dynamic_js_layer(elite_data_json)}"
    )
    prefix.extend([injected])


def _get_dynamic_js_layer(elite_data_json):
    js_content = """
    <style>
      .elite-overlay { position: fixed; inset: 0; z-index: 999999; overflow: auto; background: var(--bg-color); }
      #results-table, #results-table-head, #environment, #summary-container, #summary { display: none !important; }
      .summary__data > h2 { display: none !important; }
      .step-item { display: flex; flex-direction: column; align-items: flex-start; padding: 0.5rem 0; }
      .step-row { display: flex; width: 100%; justify-content: space-between; gap: 1rem; }
      .step-time { font-size: 0.7rem; color: var(--text-secondary); font-family: 'JetBrains Mono', monospace; }
      .step-shot { margin-top: 0.5rem; max-width: 420px; border-radius: 6px; border: 1px solid var(--border); cursor: zoom-in; }
    </style>
    <script>
      function openShot(img) { const w = window.open(''); w.document.write('<img src="' + img.src + '" style="max-width:100%">'); }
      function syncEliteReport() {
        const eliteData = [[ELITE_DATA_JSON]];
        const listContainer = document.querySelector('.test-list');
        if (!listContainer) return;
        listContainer.innerHTML = '';
        let passed = 0, failed = 0, totalTime = 0;

        eliteData.forEach((test) => {
          const status = test.outcome === 'passed' ? 'passed' : (['failed', 'error'].includes(test.outcome) ? 'failed' : 'other');
          if (status === 'passed') passed++;
          if (status === 'failed') failed++;
          totalTime += test.duration;

          const steps = test.steps || [];
          const internalId = 'log-' + Math.random().toString(36).slice(2, 11);

          const stepsHtml = steps.map(step => `
              <div class="step-item step-${step.status}">
                  <div class="step-row"><span>${step.message}</span><span class="step-time">${step.timestamp}</span></div>
                  ${step.screenshot_b64 ? `<img class="step-shot" src="data:image/png;base64,${step.screenshot_b64}" onclick="openShot(this)"/>` : ''}
              </div>`).join('');

          const expectedHtml = test.expected_result ? `
            <div style="background: rgba(120,37,111,0.05); border: 1px dashed rgba(120,37,111,0.3); border-radius: 8px; padding: 12px 16px; margin-bottom: 1rem;">
              <div style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: #78256f; margin-bottom: 4px;">📋 Resultado Esperado</div>
              <div style="font-size: 0.85rem; color: var(--text-primary); line-height: 1.4;">${test.expected_result}</div>
            </div>` : '';

          const evidenceHtml = `
            ${expectedHtml}
            <div class="step-timeline">${stepsHtml}</div>
            ${test.screenshot_b64 ? `<div style="font-size:0.75rem;font-weight:700;color:var(--text-secondary);margin-bottom:0.5rem;">PANTALLA FINAL</div>
              <div style="max-width: 100%; border-radius: 8px; border: 1px solid var(--border); overflow: hidden; margin-bottom: 1rem;">
                <img src="data:image/png;base64,${test.screenshot_b64}" style="max-width:100%; display:block; cursor:zoom-in;" onclick="openShot(this)"/>
              </div>` : ''}
            ${test.log ? `<div id="${internalId}" style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; background: #020617; color: #f43f5e; padding: 1rem; border-radius: 8px; overflow-x: auto; max-height: 400px; white-space: pre-wrap;">${test.log}</div>` : ''}
          `;

          const details = document.createElement('details');
          details.className = 'test-item';
          details.setAttribute('data-status', status);
          if (status === 'failed') details.setAttribute('open', '');
          details.innerHTML = `
            <summary>
              <div class="test-info"><div class="status-dot dot-${status}"></div>
                <p style="font-weight: 600; color: var(--text-primary);">${test.test_name}</p></div>
              <div style="display: flex; align-items: center; gap: 2rem;">
                ${status === 'failed' ? '<span style="color: var(--accent-danger); font-size: 0.75rem; font-weight: 700;">FALLO</span>' : `<span class="test-meta">${test.duration.toFixed(2)}s</span>`}
                <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
              </div>
            </summary>
            <div class="evidence-body">${evidenceHtml}</div>`;
          listContainer.appendChild(details);
        });

        const total = passed + failed;
        const s = document.querySelector('.card.success .value');
        const d = document.querySelector('.card.danger .value');
        const t = document.querySelector('.stats-grid .card:not(.success):not(.danger) .value');
        if (s) s.innerText = `${passed} / ${total}`;
        if (d) d.innerText = `${failed} / ${total}`;
        if (t) t.innerText = totalTime.toFixed(1) + 's';
        const percent = total > 0 ? Math.round((passed / total) * 100) : 0;
        const donutFill = document.querySelector('.donut-fill');
        if (donutFill) { donutFill.style.strokeDasharray = '440'; donutFill.style.strokeDashoffset = 440 - (440 * percent / 100); }
        const donutText = document.querySelector('.donut-text');
        if (donutText) donutText.innerHTML = `${percent}%<br><span style="font-size: 0.65rem; color: var(--text-secondary); font-weight: 500;">SUCCESS</span>`;
      }
      window.addEventListener('load', function () {
        document.body.setAttribute('data-theme', 'light');
        document.documentElement.setAttribute('data-theme', 'light');
        syncEliteReport();
      });
    </script>
    """
    return js_content.replace("[[ELITE_DATA_JSON]]", elite_data_json)
