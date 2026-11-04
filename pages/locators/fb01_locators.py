"""
Localizadores de SAP GUI para la transacción FB01 (Contabilización de Documentos Financieros).
"""


class FB01Locators:
    """IDs de controles SAP GUI para la transacción FB01 (Contabilización de Cuentas de Mayor)."""

    TCODE = "FB01"

    # --- Cabecera del documento (BKPF) ---
    TXT_FECHA_DOCUMENTO = "wnd[0]/usr/ctxtBKPF-BLDAT"
    TXT_CLASE_DOCUMENTO = "wnd[0]/usr/ctxtBKPF-BLART"
    TXT_SOCIEDAD = "wnd[0]/usr/ctxtBKPF-BUKRS"
    TXT_FECHA_CONTABILIZACION = "wnd[0]/usr/ctxtBKPF-BUDAT"
    TXT_MONEDA = "wnd[0]/usr/ctxtBKPF-WAERS"
    TXT_REFERENCIA = "wnd[0]/usr/txtBKPF-XBLNR"
    TXT_TEXTO_CABECERA = "wnd[0]/usr/txtBKPF-BKTXT"

    # --- Navegación / Datos de posición inicial o siguiente (RF05A) ---
    TXT_CLAVE_CONTABILIZACION = "wnd[0]/usr/ctxtRF05A-NEWBS"
    TXT_CUENTA = "wnd[0]/usr/ctxtRF05A-NEWKO"

    # --- Detalle de posición (BSEG / COBL) ---
    TXT_IMPORTE = "wnd[0]/usr/txtBSEG-WRBTR"
    TXT_INDICADOR_IMPUESTOS = "wnd[0]/usr/ctxtBSEG-MWSKZ"
    TXT_TEXTO_POSICION = "wnd[0]/usr/ctxtBSEG-SGTXT"
    POSSIBLE_COST_CENTER_IDS = [
        "wnd[0]/usr/subBLOCK:SAPLKACB:1006/ctxtCOBL-KOSTL",
        "wnd[0]/usr/subBLOCK:SAPLKACB:1002/ctxtCOBL-KOSTL",
        "wnd[0]/usr/ctxtCOBL-KOSTL",
        "wnd[0]/usr/ctxtBSEG-KOSTL",
    ]

    # --- Botones y Comandos de aplicación ---
    BTN_RESUMEN = "wnd[0]/tbar[1]/btn[14]"
    CMD_RESUMEN = "=AB"

