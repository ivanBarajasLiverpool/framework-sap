"""
Clase base `BasePage` para el patrón Page Object Model (POM) sobre SAP GUI.
Encapsula las llamadas al motor `SAPEngine` (basado en `robotframework-sapguilibrary`)
garantizando el registro de pasos, resaltado de controles, capturas Base64 para el
reporte Liverpool y manejo de buffers.
"""

from typing import Dict, List, Optional, Union
from core.sap_engine import SAPEngine
from pages.locators.common_locators import CommonLocators


class BasePage:
    """
    Superclase de todas las páginas de transacciones SAP GUI.
    Proporciona métodos atómicos de interacción, validación, barra de estado,
    menús, tablas y toma de evidencias.
    """

    def __init__(self, sap: SAPEngine):
        self.sap = sap
        self.sap_lib = sap.sap_lib

    # ==========================================================
    # NAVEGACIÓN Y COMANDOS GENERALES
    # ==========================================================
    def abrir_transaccion(self, tcode: str) -> "BasePage":
        """Inicia una transacción o comando SAP en el OKCode (`SapGuiLibrary.run_transaction`)."""
        self.sap.start_transaction(tcode)
        return self

    def presionar_enter(self, descripcion: str = "Enter") -> "BasePage":
        """Envía la tecla Enter (VKey 0) a la ventana principal (`SapGuiLibrary.send_vkey`)."""
        self.sap.press_enter(describe=descripcion)
        return self

    def guardar(self, descripcion: str = "Clic en Guardar / Contabilizar") -> "BasePage":
        """Presiona el botón estándar de Guardar / Contabilizar (`wnd[0]/tbar[0]/btn[11]`)."""
        self.sap.click_save(describe=descripcion)
        return self

    def enviar_vkey(
        self,
        vkey: Union[int, str],
        ventana: Union[int, str] = CommonLocators.MAIN_WINDOW,
        descripcion: Optional[str] = None,
    ) -> "BasePage":
        """Envía una tecla virtual (ej. 0=Enter, 3=Back, 8=Ejecutar, 12=Cancelar/ESC) usando `SapGuiLibrary.send_vkey`."""
        self.sap.send_vkey(vkey=vkey, window=ventana, describe=descripcion)
        return self

    def seleccionar_menu(self, ruta_menu: str) -> "BasePage":
        """Navega por la barra de menús de SAP usando una ruta separada por '->'."""
        self.sap.select_menu_by_path(ruta_menu)
        return self

    def seleccionar_menu_por_id(self, menu_id: str, etiqueta: Optional[str] = None) -> "BasePage":
        """Selecciona un ítem de menú directamente por su ID técnico (`SapGuiLibrary.click_element`)."""
        self.sap.select_menu_by_id(menu_id, label=etiqueta)
        return self

    def maximizar_ventana(self, ventana: Union[int, str] = 0) -> "BasePage":
        """Maximiza la ventana SAP indicada (`SapGuiLibrary.maximize_window`)."""
        self.sap.maximize_window(ventana)
        return self

    def obtener_titulo_ventana(self, ventana: Union[int, str] = CommonLocators.MAIN_WINDOW) -> str:
        """Devuelve el título de la ventana activa (`SapGuiLibrary.get_window_title`)."""
        return self.sap.get_window_title(ventana)

    # ==========================================================
    # INTERACCIÓN CON ELEMENTOS (SAPGUILIBRARY)
    # ==========================================================
    def escribir(self, locator: str, valor: str, etiqueta: Optional[str] = None) -> "BasePage":
        """Escribe texto en un campo SAP (`SapGuiLibrary.input_text`) con evidencia y resaltado."""
        self.sap.set_text(locator, valor, label=etiqueta)
        return self

    def escribir_password(self, locator: str, password: str, etiqueta: str = "Contraseña") -> "BasePage":
        """Escribe una contraseña (`SapGuiLibrary.input_password`) ocultando el valor en logs y reportes."""
        self.sap.set_password(locator, password, label=etiqueta)
        return self

    def escribir_en_id_dinamico(self, posibles_locators: List[str], valor: str, etiqueta: Optional[str] = None) -> str:
        """
        Escribe en el primer locator disponible o busca el control recursivamente por sufijo
        en subscreens dinámicos de SAP, ejecutando `SapGuiLibrary.input_text`.
        """
        return self.sap.set_text_by_Possible_ids(posibles_locators, valor, label=etiqueta)

    def clic(self, locator: str, etiqueta: Optional[str] = None) -> "BasePage":
        """Hace clic en un botón, pestaña o menú (`SapGuiLibrary.click_element`)."""
        self.sap.press_button(locator, label=etiqueta)
        return self

    def clic_boton_tabla(self, tabla_locator: str, boton_id: str, etiqueta: Optional[str] = None) -> "BasePage":
        """Presiona un botón en la barra de herramientas de un GridView (`SapGuiLibrary.click_toolbar_button`)."""
        self.sap.click_toolbar_button(tabla_locator, boton_id, label=etiqueta)
        return self

    def marcar_checkbox(self, locator: str, seleccionado: bool = True, etiqueta: Optional[str] = None) -> "BasePage":
        """Marca o desmarca un CheckBox (`SapGuiLibrary.select_checkbox` / `unselect_checkbox`)."""
        self.sap.select_checkbox(locator, selected=seleccionado, label=etiqueta)
        return self

    def seleccionar_radio_button(self, locator: str, etiqueta: Optional[str] = None) -> "BasePage":
        """Selecciona un RadioButton (`SapGuiLibrary.select_radio_button`)."""
        self.sap.select_radio_button(locator, label=etiqueta)
        return self

    def seleccionar_combo(self, locator: str, valor: str, etiqueta: Optional[str] = None) -> "BasePage":
        """Selecciona una opción en un ComboBox por su etiqueta (`SapGuiLibrary.select_from_list_by_label`)."""
        self.sap.select_from_list_by_label(locator, valor, label=etiqueta)
        return self

    def obtener_valor(self, locator: str) -> str:
        """Lee y retorna el valor o texto de un control (`SapGuiLibrary.get_value`)."""
        return self.sap.get_value(locator)

    # ==========================================================
    # TABLAS Y GRIDVIEWS (SAPGUILIBRARY)
    # ==========================================================
    def obtener_valor_celda(self, tabla_locator: str, fila: int, columna_id: str) -> str:
        """Obtiene el valor de una celda en un GridView (`SapGuiLibrary.get_cell_value`)."""
        return self.sap.get_cell_value(tabla_locator, fila, columna_id)

    def escribir_en_celda(
        self,
        tabla_locator: str,
        fila: int,
        columna_id: str,
        valor: str,
        etiqueta: Optional[str] = None,
    ) -> "BasePage":
        """Modifica el valor de una celda en un GridView (`SapGuiLibrary.set_cell_value`)."""
        self.sap.set_cell_value(tabla_locator, fila, columna_id, valor, label=etiqueta)
        return self

    def seleccionar_fila_tabla(self, tabla_locator: str, fila: int, etiqueta: Optional[str] = None) -> "BasePage":
        """Selecciona una fila en un TableControl o GridView (`SapGuiLibrary.select_table_row`)."""
        self.sap.select_table_row(tabla_locator, fila, label=etiqueta)
        return self

    def contar_filas_tabla(self, tabla_locator: str) -> int:
        """Obtiene el total de filas de un GridView (`SapGuiLibrary.get_row_count`)."""
        return self.sap.get_row_count(tabla_locator)

    # ==========================================================
    # ASERCIONES Y VALIDACIONES DE CONTROLES (SAPGUILIBRARY)
    # ==========================================================
    def verificar_elemento_presente(self, locator: str, mensaje: Optional[str] = None) -> "BasePage":
        """Valida que un elemento exista en la pantalla (`SapGuiLibrary.element_should_be_present`)."""
        self.sap.element_should_be_present(locator, message=mensaje)
        return self

    def verificar_valor_elemento(self, locator: str, valor_esperado: str, mensaje: Optional[str] = None) -> "BasePage":
        """Valida que el valor de un elemento coincida exactamente (`SapGuiLibrary.element_value_should_be`)."""
        self.sap.element_value_should_be(locator, valor_esperado, message=mensaje)
        return self

    def verificar_elemento_contiene(self, locator: str, texto_esperado: str, mensaje: Optional[str] = None) -> "BasePage":
        """Valida que el valor de un elemento contenga el texto esperado (`SapGuiLibrary.element_value_should_contain`)."""
        self.sap.element_value_should_contain(locator, texto_esperado, message=mensaje)
        return self

    # ==========================================================
    # BARRA DE ESTADO, BUFFERS Y EVIDENCIAS
    # ==========================================================
    def obtener_info_barra_estado(self) -> Dict[str, str]:
        """Devuelve un diccionario con `text`, `type`, `id`, `number` y `parameter_1` de la barra de estado."""
        return self.sap.get_statusbar_info()

    def capturar_documento_de_barra_estado(
        self,
        buffer_name: str = "NumDocContable",
        expected_text_contains: str = "se contabilizó",
    ) -> str:
        """Valida la barra de estado tras contabilizar, guarda el Nº de documento en un buffer y lo retorna."""
        return self.sap.buffer_statusbar_doc_number(
            buffer_name=buffer_name,
            expected_text_contains=expected_text_contains,
        )

    def guardar_buffer(self, nombre: str, valor: str) -> "BasePage":
        """Almacena un valor en los buffers de la sesión."""
        self.sap.set_buffer(nombre, valor)
        return self

    def obtener_buffer(self, nombre: str) -> str:
        """Recupera un valor previamente almacenado en los buffers de la sesión."""
        return self.sap.get_buffer(nombre)

    def registrar_paso(self, mensaje: str, estado: str = "passed") -> "BasePage":
        """Registra manualmente un paso en la línea de tiempo del reporte HTML Liverpool."""
        self.sap.step(mensaje, status=estado)
        return self

    def tomar_evidencia(self, nombre_paso: str) -> str:
        """Guarda una captura PNG en la carpeta `reports/` y devuelve la ruta."""
        return self.sap.take_screenshot(nombre_paso)

