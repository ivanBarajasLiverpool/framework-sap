"""
Script de scraping e inspección de objetos SAP GUI para el Subagente `sap-scraper`.
Permite conectarse a la sesión activa de SAP GUI (o iniciar sesión con SAPEngine.from_config()),
navegar opcionalmente a una transacción, escribir campos / enviar teclas para avanzar de pantalla
y volcar el árbol completo de controles (ID relativo `wnd[0]/...`, Tipo, Nombre, Texto, Tooltip).

Ejemplos de uso desde terminal por el subagente `sap-scraper`:
  1. Inspeccionar la ventana actual en formato tabla Markdown:
     python .agents/skills/sap-orchestrator/scripts/sap_gui_scraper.py

  2. Abrir una transacción e inspeccionar todos sus campos:
     python .agents/skills/sap-orchestrator/scripts/sap_gui_scraper.py --tcode FB01

  3. Llenar campos de cabecera, presionar Enter (VKey 0) e inspeccionar la siguiente pantalla:
     python .agents/skills/sap-orchestrator/scripts/sap_gui_scraper.py ^
       --set "wnd[0]/usr/ctxtBKPF-BLDAT=14.10.2026" ^
       --set "wnd[0]/usr/ctxtBKPF-BLART=SA" ^
       --set "wnd[0]/usr/ctxtBKPF-BUKRS=110" ^
       --set "wnd[0]/usr/ctxtBKPF-BUDAT=14.10.2026" ^
       --set "wnd[0]/usr/ctxtBKPF-WAERS=MXP" ^
       --set "wnd[0]/usr/ctxtRF05A-NEWBS=40" ^
       --set "wnd[0]/usr/ctxtRF05A-NEWKO=51000271" ^
       --vkey 0
"""

import os
import re
import sys
import json
import argparse
from typing import List, Dict, Any

# Agregar la raíz del proyecto al sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from core.sap_engine import SAPEngine


INTERACTIVE_TYPES = {
    "GuiTextField",
    "GuiCTextField",
    "GuiPasswordField",
    "GuiOkCodeField",
    "GuiButton",
    "GuiCheckBox",
    "GuiRadioButton",
    "GuiComboBox",
    "GuiTab",
    "GuiTableControl",
    "GuiShell",
    "GuiGridView",
    "GuiStatusbar",
    "GuiLabel",
}


def _relative_id(raw_id: str) -> str:
    """Convierte '/app/con[0]/ses[0]/wnd[0]/usr/...' a 'wnd[0]/usr/...'."""
    return re.sub(r"^/app/con\[\d+\]/ses\[\d+\]/", "", str(raw_id or ""))


def _collect_controls(container, results: List[Dict[str, Any]], include_labels: bool = False):
    """Recorre recursivamente el árbol COM de SAP GUI extrayendo metadatos de cada control."""
    try:
        ctrl_type = getattr(container, "Type", "")
        raw_id = getattr(container, "Id", "")
        rel_id = _relative_id(raw_id)

        if ctrl_type in INTERACTIVE_TYPES:
            if ctrl_type != "GuiLabel" or include_labels:
                item = {
                    "id": rel_id,
                    "type": ctrl_type,
                    "name": getattr(container, "Name", ""),
                    "text": getattr(container, "Text", ""),
                    "tooltip": getattr(container, "Tooltip", ""),
                    "changeable": getattr(container, "Changeable", None),
                }
                results.append(item)
    except Exception:
        pass

    try:
        children = getattr(container, "Children", None)
        if children is not None:
            for i in range(children.Count):
                _collect_controls(children(i), results, include_labels=include_labels)
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="Inspector / Scraper de controles SAP GUI.")
    parser.add_argument("--tcode", help="Transacción SAP a ejecutar antes de inspeccionar (ej. FB01, FB03).")
    parser.add_argument(
        "--set",
        action="append",
        default=[],
        help="Asignación locator=valor antes de inspeccionar (puede repetirse varias veces).",
    )
    parser.add_argument(
        "--click",
        action="append",
        default=[],
        help="Locator de botón/elemento a clicar antes de inspeccionar.",
    )
    parser.add_argument(
        "--vkey",
        type=int,
        help="Tecla virtual SAP (ej. 0=Enter, 8=F8, 11=Guardar) a enviar después de --set/--click.",
    )
    parser.add_argument(
        "--window",
        default="wnd[0]",
        help="Ventana a inspeccionar (por defecto wnd[0], o wnd[1] para pop-ups).",
    )
    parser.add_argument(
        "--include-labels",
        action="store_true",
        help="Incluir controles GuiLabel en el volcado.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Imprimir la salida en formato JSON estructurado en lugar de tabla Markdown.",
    )
    args = parser.parse_args()

    engine = SAPEngine.from_config()
    session = engine.session

    if args.tcode:
        engine.start_transaction(args.tcode)

    for pair in args.set:
        if "=" not in pair:
            raise ValueError(f"Formato inválido en --set '{pair}'. Usa locator=valor.")
        locator, value = pair.split("=", 1)
        engine.set_text(locator.strip(), value.strip())

    for btn in args.click:
        engine.press_button(btn.strip())

    if args.vkey is not None:
        engine.send_vkey(args.vkey)

    target_window = session.findById(args.window)
    win_title = getattr(target_window, "Text", "")
    program = getattr(session.Info, "Program", "")
    screen_number = getattr(session.Info, "ScreenNumber", "")
    transaction = getattr(session.Info, "Transaction", "")

    controls: List[Dict[str, Any]] = []
    _collect_controls(target_window, controls, include_labels=args.include_labels)

    payload = {
        "window": args.window,
        "title": win_title,
        "transaction": transaction,
        "program": program,
        "screen_number": screen_number,
        "controls_count": len(controls),
        "controls": controls,
    }

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    print(f"### Ventana: `{args.window}` — {win_title}")
    print(f"- **Transacción activa**: `{transaction}` | **Programa**: `{program}` | **Dynpro**: `{screen_number}`")
    print(f"- **Total de controles detectados**: `{len(controls)}`\n")
    print("| ID Relativo (`locator`) | Tipo (`Type`) | Nombre Técnico (`Name`) | Texto / Valor | Tooltip | Editable |")
    print("| :--- | :--- | :--- | :--- | :--- | :---: |")
    for c in controls:
        loc = c["id"]
        ctype = c["type"]
        name = c["name"]
        txt = str(c["text"] or "").replace("\n", " ").replace("|", "\\|")[:45]
        tip = str(c["tooltip"] or "").replace("\n", " ").replace("|", "\\|")[:55]
        chg = "Sí" if c["changeable"] else ("No" if c["changeable"] is False else "-")
        print(f"| `{loc}` | `{ctype}` | `{name}` | {txt} | {tip} | {chg} |")


if __name__ == "__main__":
    main()

