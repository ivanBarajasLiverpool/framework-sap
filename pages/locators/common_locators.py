"""
Localizadores comunes de SAP GUI (Ventana principal, barras de herramientas, barra de estado, login y menús).
"""


class CommonLocators:
    """IDs técnicos de controles transversales a todas las pantallas de SAP GUI."""

    # --- Ventanas ---
    MAIN_WINDOW = "wnd[0]"
    POPUP_WINDOW = "wnd[1]"
    USER_AREA = "wnd[0]/usr"

    # --- Barra de comandos y botones estándar (Toolbar 0) ---
    OK_CODE = "wnd[0]/tbar[0]/okcd"
    BTN_ENTER = "wnd[0]/tbar[0]/btn[0]"
    BTN_SAVE = "wnd[0]/tbar[0]/btn[11]"
    BTN_BACK = "wnd[0]/tbar[0]/btn[3]"
    BTN_EXIT = "wnd[0]/tbar[0]/btn[15]"
    BTN_CANCEL = "wnd[0]/tbar[0]/btn[12]"

    # --- Barra de menú y Barra de estado ---
    MENU_BAR = "wnd[0]/mbar"
    STATUS_BAR = "wnd[0]/sbar"

    # --- Diálogos de confirmación (SPOP) ---
    BTN_POPUP_YES = "wnd[1]/usr/btnSPOP-OPTION1"
    BTN_POPUP_NO = "wnd[1]/usr/btnSPOP-OPTION2"


class LoginLocators:
    """IDs técnicos de la pantalla de inicio de sesión de SAP GUI y pop-ups posteriores."""

    TXT_CLIENT = "wnd[0]/usr/txtRSYST-MANDT"
    TXT_USER = "wnd[0]/usr/txtRSYST-BNAME"
    PWD_PASSWORD = "wnd[0]/usr/pwdRSYST-BCODE"
    TXT_LANGUAGE = "wnd[0]/usr/txtRSYST-LANGU"

    # --- Pop-up de Logon Múltiple y Avisos del Sistema ---
    RAD_MULTI_LOGON_CONTINUE = "wnd[1]/usr/radMULTI_LOGON_OPT2"
    BTN_POPUP_CONFIRM = "wnd[1]/tbar[0]/btn[0]"
