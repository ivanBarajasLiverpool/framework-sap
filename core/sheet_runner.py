import sys
import pandas as pd
from core.sap_engine import SAPEngine, logger


def run_from_sheet(file_path: str):
    """
    Lee un archivo CSV o Excel (.xlsx) con el formato de matriz a bajo nivel
    y ejecuta cada fila automáticamente sobre SAP GUI.
    """
    df = pd.read_excel(file_path) if file_path.endswith(".xlsx") else pd.read_csv(file_path, dtype=str)
    df = df.fillna("")

    sap = SAPEngine()
    logger.info(f"Iniciando ejecución Data-Driven desde: {file_path} ({len(df)} pasos)")

    for _, row in df.iterrows():
        paso = row.get("Paso", "")
        accion = row.get("Accion", "").strip().upper()
        control_id = row.get("Control_o_Ruta", "").strip()
        insumo = str(row.get("Insumo", "")).strip()
        validacion = str(row.get("Validacion_Esperada", "")).strip()

        logger.info(f"--- Ejecutando Paso {paso}: {accion} | {control_id} ---")

        if accion == "TRANSACCION":
            sap.start_transaction(insumo)
        elif accion == "INPUT":
            sap.set_text(control_id, insumo)
        elif accion == "INPUT_MULTI_ID":
            ids = [x.strip() for x in control_id.split("|")]
            sap.set_text_by_Possible_ids(ids, insumo)
        elif accion == "ENTER":
            sap.press_enter()
        elif accion == "CLICK":
            sap.press_button(control_id)
        elif accion == "SAVE":
            sap.click_save()
        elif accion == "MENU":
            sap.select_menu_by_path(control_id)
        elif accion == "BUFFER_STATUSBAR":
            sap.buffer_statusbar_doc_number(buffer_name=insumo, expected_text_contains=validacion)
        elif accion == "CAPTURAR_POPUP_FINANZAS":
            sap.extract_popup_documents_list(window_id=control_id or "wnd[1]")
            sap.take_screenshot(f"Paso_{paso}_Popup_Finanzas")
            sap.send_vkey(12, window=control_id or "wnd[1]")
        elif accion == "SCREENSHOT":
            sap.take_screenshot(f"Paso_{paso}_{insumo}")
        else:
            raise ValueError(f"Acción no reconocida en el Paso {paso}: {accion}")

    logger.info("====================================================")
    logger.info("EJECUCIÓN FINALIZADA CON ÉXITO. BUFFERS CAPTURADOS:")
    for k, v in sap.buffers.items():
        logger.info(f"  * {k}: {v}")
    logger.info("====================================================")
    return sap.buffers


if __name__ == "__main__":
    archivo = sys.argv[1] if len(sys.argv) > 1 else "data/matriz_fb01.csv"
    run_from_sheet(archivo)
