"""
Localizadores y rutas de menú de SAP GUI para la transacción FB03 (Visualización de Documentos).
"""


class FB03Locators:
    """Rutas de menú e IDs de controles para FB03 (Visualización de Documentos Financieros)."""

    TCODE = "FB03"

    # --- Pantalla inicial de FB03 ---
    TXT_NUM_DOCUMENTO = "wnd[0]/usr/txtRF05L-BELNR"
    TXT_SOCIEDAD = "wnd[0]/usr/ctxtRF05L-BUKRS"
    TXT_EJERCICIO = "wnd[0]/usr/txtRF05L-GJAHR"

    # --- Rutas de menú ---
    MENU_DOCUMENTO_VISUALIZAR = "Documento->Visualizar"
    MENU_DOCUMENTOS_FINANCIEROS = "Entorno->Entorno de documento->Documentos financieros"

    # --- Ventana emergente de Documentos en Finanzas ---
    POPUP_FINANZAS_WINDOW_ID = "wnd[1]"

