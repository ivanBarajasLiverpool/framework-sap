"""
Page Object Model (`FB03Page`) para la transacción SAP FB03 (Visualización de Documentos Financieros).
Construido sobre `BasePage` y `robotframework-sapguilibrary`.
"""

from typing import Dict, Any, List, Optional
from pages.modules.base_page import BasePage
from pages.locators.fb03_locators import FB03Locators


class FB03Page(BasePage):
    """
    Page Object de la transacción FB03 (Visualizar documento).
    Permite abrir un documento desde el menú o por código de transacción,
    consultar el entorno de Documentos Financieros y validar los documentos generados.
    """

    def abrir(
        self,
        num_documento: Optional[str] = None,
        sociedad: Optional[str] = None,
        ejercicio: Optional[str] = None,
    ) -> "FB03Page":
        """
        Abre la transacción FB03 directamente y, si se indican parámetros,
        consulta el documento especificado.
        """
        self.abrir_transaccion(FB03Locators.TCODE)
        if num_documento:
            self.escribir(FB03Locators.TXT_NUM_DOCUMENTO, num_documento, "Nº documento")
        if sociedad:
            self.escribir(FB03Locators.TXT_SOCIEDAD, sociedad, "Sociedad")
        if ejercicio:
            self.escribir(FB03Locators.TXT_EJERCICIO, ejercicio, "Ejercicio")
        if num_documento or sociedad or ejercicio:
            self.presionar_enter("Visualizar documento en FB03")
        return self

    def abrir_desde_menu_documento(self) -> "FB03Page":
        """Navega a 'Documento -> Visualizar' desde la barra de menú superior de SAP."""
        self.seleccionar_menu(FB03Locators.MENU_DOCUMENTO_VISUALIZAR)
        return self

    def abrir_entorno_documentos_financieros(self) -> "FB03Page":
        """Navega a 'Entorno -> Entorno de documento -> Documentos financieros'."""
        self.seleccionar_menu(FB03Locators.MENU_DOCUMENTOS_FINANCIEROS)
        return self

    def extraer_documentos_popup_finanzas(self) -> List[Dict[str, str]]:
        """Extrae la lista de documentos financieros mostrada en la ventana modal `wnd[1]`."""
        return self.sap.extract_popup_documents_list(window_id=FB03Locators.POPUP_FINANZAS_WINDOW_ID)

    def cerrar_popup_finanzas(self) -> "FB03Page":
        """Cierra la ventana emergente de documentos financieros enviando VKey 12 (Cancelar/ESC)."""
        self.enviar_vkey(
            12,
            ventana=FB03Locators.POPUP_FINANZAS_WINDOW_ID,
            descripcion="Cerrar pop-up Documentos en Finanzas",
        )
        return self

    def visualizar_documentos_financieros(
        self,
        buffer_name: str = "NumDocContable",
    ) -> Dict[str, Any]:
        """
        Navega desde el documento recién contabilizado a su visualización y extrae
        todos los documentos financieros del pop-up de entorno.
        """
        self.abrir_desde_menu_documento()
        self.abrir_entorno_documentos_financieros()
        docs = self.extraer_documentos_popup_finanzas()
        self.cerrar_popup_finanzas()

        return {
            "num_doc_contabilizado": self.obtener_buffer(buffer_name),
            "documentos_financieros": docs,
            "todos_los_buffers": dict(self.sap.buffers),
        }

    def validar_documentos_financieros(
        self,
        min_documentos: int = 1,
        buffer_name: str = "NumDocContable",
    ) -> Dict[str, Any]:
        """
        Ejecuta la visualización de documentos financieros en FB03 y valida que
        se hayan generado al menos `min_documentos` documentos.
        """
        resultado = self.visualizar_documentos_financieros(buffer_name=buffer_name)
        docs = resultado.get("documentos_financieros", [])

        assert len(docs) >= min_documentos, (
            f"Validación fallida en FB03: Se esperaban al menos {min_documentos} documentos financieros, "
            f"pero se obtuvieron {len(docs)}. Documentos obtenidos: {docs}"
        )
        return resultado

    # --- Aliases de compatibilidad ---
    visualizar_documentos_financieros_fb03 = visualizar_documentos_financieros
    validar_documentos_financieros_generados = validar_documentos_financieros
    validar_documentos_financieros_fb03 = validar_documentos_financieros

