"""
Page Object para la pantalla de inicio de sesión de SAP GUI (`LoginPage`).
"""

import time
from pages.modules.base_page import BasePage
from pages.locators.common_locators import LoginLocators


class LoginPage(BasePage):
    """
    Encapsula la interacción con la pantalla de autenticación de SAP Logon
    utilizando los métodos de `SapGuiLibrary` a través de `BasePage`,
    incluyendo el manejo automático de pop-ups de logon múltiple y validación de errores.
    """

    def iniciar_sesion(
        self,
        mandante: str,
        usuario: str,
        password: str,
        idioma: str = "ES",
    ) -> "LoginPage":
        """
        Completa las credenciales en la ventana de login de SAP GUI, presiona Enter,
        resuelve posibles diálogos de sesión múltiple y verifica que no existan errores de acceso.
        """
        self.maximizar_ventana(0)
        self.escribir(LoginLocators.TXT_CLIENT, str(mandante), "Mandante")
        self.escribir(LoginLocators.TXT_USER, str(usuario), "Usuario")
        self.escribir_password(LoginLocators.PWD_PASSWORD, str(password), "Contraseña")
        self.escribir(LoginLocators.TXT_LANGUAGE, str(idioma), "Idioma")
        self.presionar_enter("Confirmar inicio de sesión SAP")
        self.resolver_popups_post_login()
        self.validar_login_exitoso()
        return self

    def resolver_popups_post_login(self) -> "LoginPage":
        """
        Gestiona posibles pop-ups posteriores al login:
        1. Pop-up de Logon Múltiple (selecciona continuar con este logon).
        2. Pop-up de mensajes informativos del sistema.
        """
        try:
            self.seleccionar_radio_button(
                LoginLocators.RAD_MULTI_LOGON_CONTINUE,
                "Continuar con este logon",
            )
            self.clic(LoginLocators.BTN_POPUP_CONFIRM, "Confirmar logon múltiple")
            time.sleep(0.5)
        except Exception:
            pass

        try:
            self.clic(LoginLocators.BTN_POPUP_CONFIRM, "Aceptar aviso del sistema")
        except Exception:
            pass
        return self

    def validar_login_exitoso(self) -> "LoginPage":
        """Verifica que la barra de estado no reporte un mensaje de error ('E' o 'A') tras iniciar sesión."""
        sbar = self.obtener_info_barra_estado()
        if sbar.get("type") in ("E", "A"):
            raise RuntimeError(f"SAP devolvió error al iniciar sesión: {sbar.get('text')}")
        return self
