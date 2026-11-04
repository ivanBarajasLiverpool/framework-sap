"""
Page Object Model (`FB01Page`) para la transacción SAP FB01 (Contabilización de Documentos Financieros).
Construido sobre `BasePage` y `robotframework-sapguilibrary`.
"""

from typing import Dict, Any
from pages.modules.base_page import BasePage
from pages.locators.fb01_locators import FB01Locators


class FB01Page(BasePage):
    """
    Page Object de la transacción FB01 (Contabilizar documento).
    Proporciona métodos modulares y encadenables para ingresar la cabecera,
    las posiciones contables (Debe/Haber), visualizar el resumen y contabilizar.
    """

    def abrir(self) -> "FB01Page":
        """Inicia la transacción FB01 en SAP GUI."""
        self.abrir_transaccion(FB01Locators.TCODE)
        return self

    def completar_cabecera(
        self,
        fecha_doc: str,
        clase_doc: str,
        sociedad: str,
        fecha_contab: str,
        moneda: str,
    ) -> "FB01Page":
        """Completa los campos de cabecera del documento contable (BKPF) en FB01."""
        self.escribir(FB01Locators.TXT_FECHA_DOCUMENTO, fecha_doc, "Fecha documento")
        self.escribir(FB01Locators.TXT_CLASE_DOCUMENTO, clase_doc, "Clase")
        self.escribir(FB01Locators.TXT_SOCIEDAD, sociedad, "Sociedad")
        self.escribir(FB01Locators.TXT_FECHA_CONTABILIZACION, fecha_contab, "Fecha contab.")
        self.escribir(FB01Locators.TXT_MONEDA, moneda, "Moneda")
        return self

    def iniciar_posicion(
        self,
        clave_contab: str = "40",
        cuenta: str = "",
        descripcion_enter: str = "Enter → Posición 1 (Debe 40)",
    ) -> "FB01Page":
        """Ingresa la clave de contabilización y cuenta en el pie de página y presiona Enter."""
        self.escribir(FB01Locators.TXT_CLAVE_CONTABILIZACION, clave_contab, "ClvCT (1ª posición)")
        self.escribir(FB01Locators.TXT_CUENTA, cuenta, "Cuenta (1ª posición)")
        self.presionar_enter(descripcion_enter)
        return self

    def ingresar_cabecera_y_primera_posicion(
        self,
        fecha_doc: str,
        clase_doc: str,
        sociedad: str,
        fecha_contab: str,
        moneda: str,
        clv_ct_1: str = "40",
        cuenta_1: str = "",
        iniciar_transaccion: bool = True,
    ) -> "FB01Page":
        """
        Abre (opcionalmente) la transacción FB01, llena la cabecera del documento
        y navega al detalle de la primera posición contable.
        """
        if iniciar_transaccion:
            self.abrir()
        self.completar_cabecera(
            fecha_doc=fecha_doc,
            clase_doc=clase_doc,
            sociedad=sociedad,
            fecha_contab=fecha_contab,
            moneda=moneda,
        )
        self.iniciar_posicion(
            clave_contab=clv_ct_1,
            cuenta=cuenta_1,
            descripcion_enter=f"Enter → Posición 1 (Debe {clv_ct_1})",
        )
        return self

    def ingresar_posicion_debe(
        self,
        importe: str,
        ind_impuestos: str,
        centro_costo: str,
        sig_clv_ct: str = "50",
        sig_cuenta: str = "",
    ) -> "FB01Page":
        """
        Completa el detalle de la posición 1 (Debe) con centro de costo (resolviendo
        subscreens dinámicos COBL) y prepara la siguiente posición (Haber).
        """
        self.escribir(FB01Locators.TXT_IMPORTE, importe, "Importe (Debe)")
        self.escribir(FB01Locators.TXT_INDICADOR_IMPUESTOS, ind_impuestos, "Ind. impuestos")
        self.escribir_en_id_dinamico(
            FB01Locators.POSSIBLE_COST_CENTER_IDS,
            centro_costo,
            "Centro de coste",
        )
        self.escribir(FB01Locators.TXT_CLAVE_CONTABILIZACION, sig_clv_ct, "ClvCT (siguiente)")
        self.escribir(FB01Locators.TXT_CUENTA, sig_cuenta, "Cuenta (siguiente)")
        self.presionar_enter(f"Enter → Posición 2 (Haber {sig_clv_ct})")
        return self

    def ingresar_posicion_haber_y_resumen(self, importe: str) -> "FB01Page":
        """
        Completa el importe de la posición 2 (Haber) y navega a la vista de Resumen del documento.
        """
        self.escribir(FB01Locators.TXT_IMPORTE, importe, "Importe (Haber)")
        try:
            self.clic(FB01Locators.BTN_RESUMEN, "Visualizar resumen")
        except Exception:
            self.abrir_transaccion(FB01Locators.CMD_RESUMEN)
        return self

    def contabilizar_documento(
        self,
        buffer_name: str = "NumDocContable",
        expected_text_contains: str = "se contabilizó",
    ) -> str:
        """
        Presiona Guardar / Contabilizar, valida el mensaje en la barra de estado,
        almacena el número de documento en el buffer indicado y lo devuelve.
        """
        self.guardar("Clic en Guardar / Contabilizar")
        return self.capturar_documento_de_barra_estado(
            buffer_name=buffer_name,
            expected_text_contains=expected_text_contains,
        )

    def ejecutar_flujo_completo(
        self,
        cabecera: Dict[str, Any],
        posicion_debe: Dict[str, Any],
        posicion_haber: Dict[str, Any],
        buffer_name: str = "NumDocContable",
    ) -> str:
        """
        Ejecuta el flujo punta a punta de contabilización en FB01 a partir de diccionarios de datos.
        """
        self.ingresar_cabecera_y_primera_posicion(
            fecha_doc=cabecera["fecha_doc"],
            clase_doc=cabecera["clase_doc"],
            sociedad=cabecera["sociedad"],
            fecha_contab=cabecera["fecha_contab"],
            moneda=cabecera["moneda"],
            clv_ct_1=cabecera.get("clv_ct_1", "40"),
            cuenta_1=cabecera["cuenta_1"],
            iniciar_transaccion=cabecera.get("iniciar_transaccion", True),
        )
        self.ingresar_posicion_debe(
            importe=posicion_debe["importe"],
            ind_impuestos=posicion_debe["ind_impuestos"],
            centro_costo=posicion_debe["centro_costo"],
            sig_clv_ct=posicion_debe.get("sig_clv_ct", "50"),
            sig_cuenta=posicion_debe["sig_cuenta"],
        )
        self.ingresar_posicion_haber_y_resumen(importe=posicion_haber["importe"])
        return self.contabilizar_documento(buffer_name=buffer_name)

    # --- Aliases semánticos para fluidez y compatibilidad ---
    completar_posicion_debe = ingresar_posicion_debe
    completar_posicion_haber_y_abrir_resumen = ingresar_posicion_haber_y_resumen
    contabilizar_y_obtener_documento = contabilizar_documento
    llenar_cabecera_y_primera_posicion = ingresar_cabecera_y_primera_posicion
    llenar_posicion_1_debe = ingresar_posicion_debe
    llenar_posicion_2_haber_y_resumen = ingresar_posicion_haber_y_resumen
    contabilizar_y_capturar_documento = contabilizar_documento

