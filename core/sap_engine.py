import os
import re
import time
import logging
import subprocess
from datetime import datetime
from typing import Dict, Optional, List, Union, Any
import win32com.client
from PIL import ImageGrab
from SapGuiLibrary import SapGuiLibrary

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("SAPEngine")


class SAPEngine:
    """
    Motor envolvente (Wrapper) sobre `robotframework-sapguilibrary` (SapGuiLibrary) y SAP GUI Scripting COM API.
    Combina todos los keywords nativos de SapGuiLibrary con:
      - Toma de evidencias paso a paso en Base64 para el reporte HTML Liverpool.
      - Resaltado visual de campos (Visualize) antes de interactuar.
      - Manejo de buffers tipo Tosca ({XB[...]}).
      - Búsqueda dinámica de controles en subscreens variables.
    """

    def __init__(
        self,
        connection_index: int = 0,
        session_index: int = 0,
        evidence_dir: str = "reports",
        sap_lib: Optional[SapGuiLibrary] = None,
    ):
        self.connection_index = connection_index
        self.session_index = session_index
        self.evidence_dir = evidence_dir
        self.buffers: Dict[str, str] = {}
        os.makedirs(self.evidence_dir, exist_ok=True)

        # Instanciar SapGuiLibrary desactivando las capturas de Robot Framework
        # para delegar toda la evidencia al motor Base64 / Nexus del repositorio.
        self.sap_lib: SapGuiLibrary = sap_lib or SapGuiLibrary(
            screenshots_on_error=False,
            screenshot_directory=self.evidence_dir,
        )
        self.sap_lib.disable_screenshots_on_error()
        self.session = self._attach_session()

    @staticmethod
    def _normalize_window_index(window: Union[int, str] = 0) -> int:
        """Convierte 'wnd[0]', 'wnd[1]' o un entero al índice numérico esperado por SapGuiLibrary."""
        if isinstance(window, int):
            return window
        match = re.search(r"\d+", str(window))
        return int(match.group(0)) if match else 0

    @staticmethod
    def _normalize_window_id(window: Union[int, str] = "wnd[0]") -> str:
        """Convierte un índice entero (0, 1) o string ('wnd[0]') al ID completo 'wnd[n]'."""
        if isinstance(window, int) or str(window).isdigit():
            return f"wnd[{window}]"
        return str(window)

    def _attach_session(self):
        """
        Conecta con la sesión activa de SAP GUI utilizando `SapGuiLibrary.connect_to_session()`,
        maximiza la ventana y sincroniza los metadatos del sistema con el reporte HTML.
        """
        try:
            self.sap_lib.connect_to_session()
            application = self.sap_lib.sapapp
            if application == -1 or getattr(application, "Children", None) is None or application.Children.Count == 0:
                raise RuntimeError(
                    "SAP Logon está abierto pero no hay ninguna conexión iniciada (Children.Count == 0).\n"
                    "-> Si usas SAP_MODE=attach: Abre el sistema en SAP Logon e inicia sesión antes de ejecutar pytest.\n"
                    "-> Si deseas automatizar el acceso: Configura SAP_MODE=login con SAP_SYSTEM, SAP_USER y SAP_PASS en tu archivo .env."
                )
            self.sap_lib.connection = application.Children(self.connection_index)
            self.sap_lib.session = self.sap_lib.connection.Children(self.session_index)
            session = self.sap_lib.session

            try:
                wnd = session.findById("wnd[0]")
                wnd.iconify()
                self.sap_lib.maximize_window(0)
            except Exception:
                pass

            info = session.Info
            logger.info(
                f"Conectado a SAP vía SapGuiLibrary: Sistema={info.SystemName}, "
                f"Mandante={info.Client}, Usuario={info.User}"
            )
            try:
                from utils.report_template import set_session_info
                set_session_info(system=info.SystemName, client=info.Client, user=info.User)
            except Exception:
                pass

            return session
        except Exception as e:
            raise RuntimeError(
                "No se pudo conectar con SAP GUI mediante SapGuiLibrary. Verifica que SAP Logon esté abierto "
                "con sesión iniciada y que SAP GUI Scripting esté habilitado. Detalle: " + str(e)
            )

    @classmethod
    def from_config(cls) -> "SAPEngine":
        """
        Crea o conecta a la sesión de SAP según la configuración de config.settings.Config:
        - Si SAP_MODE == 'login': Inicia SAP Logon y realiza login automatizado con SapGuiLibrary.
        - Si SAP_MODE == 'attach': Se conecta a la sesión ya abierta y maximiza la ventana.
        """
        try:
            from config.settings import Config
            mode = getattr(Config, "SAP_MODE", "attach").lower()
            conn_idx = getattr(Config, "SAP_CONNECTION_INDEX", 0)
            sess_idx = getattr(Config, "SAP_SESSION_INDEX", 0)
        except Exception:
            mode = "attach"
            conn_idx, sess_idx = 0, 0

        if mode == "login":
            from config.settings import Config
            missing = [k for k in ("SAP_SYSTEM", "SAP_CLIENT", "SAP_USER", "SAP_PASS") if not getattr(Config, k, None)]
            if missing:
                logger.warning(f"SAP_MODE=login pero faltan credenciales en .env ({missing}). Intentando attach a sesión activa...")
                return cls(connection_index=conn_idx, session_index=sess_idx)
            return cls.launch_sap_and_login(
                system_name=Config.SAP_SYSTEM,
                client=Config.SAP_CLIENT,
                user=Config.SAP_USER,
                password=Config.SAP_PASS,
                language=getattr(Config, "SAP_LANGUAGE", "ES"),
                saplogon_path=getattr(Config, "SAP_LOGON_PATH", r"C:\Program Files (x86)\SAP\FrontEnd\SAPgui\saplogon.exe"),
            )
        return cls(connection_index=conn_idx, session_index=sess_idx)

    @staticmethod
    def launch_sap_and_login(
        system_name: str,
        client: str,
        user: str,
        password: str,
        language: str = "ES",
        saplogon_path: str = r"C:\Program Files (x86)\SAP\FrontEnd\SAPgui\saplogon.exe",
    ) -> "SAPEngine":
        """
        Abre el ejecutable saplogon.exe si no está corriendo, abre la conexión al sistema SAP
        usando `SapGuiLibrary.open_connection`, realiza el login con `input_text` / `input_password`
        y devuelve la instancia configurada de SAPEngine.
        """
        sap_lib = SapGuiLibrary(screenshots_on_error=False)
        sap_lib.disable_screenshots_on_error()

        try:
            sap_lib.connect_to_session()
        except Exception:
            logger.info(f"Iniciando SAP Logon desde: {saplogon_path}")
            subprocess.Popen([saplogon_path])
            for _ in range(20):
                time.sleep(1)
                try:
                    sap_lib.connect_to_session()
                    break
                except Exception:
                    continue
            else:
                raise RuntimeError("No se pudo iniciar SAP Logon automáticamente.")

        logger.info(f"Abriendo conexión SAP Logon vía SapGuiLibrary: '{system_name}'")
        for attempt in range(5):
            try:
                sap_lib.open_connection(system_name)
                break
            except Exception as e:
                if attempt == 4:
                    raise
                logger.warning(f"Intento {attempt + 1}/5 al conectar a '{system_name}': {e}")
                time.sleep(1.5)

        engine = SAPEngine(0, 0, sap_lib=sap_lib)
        from pages.modules.login_page import LoginPage
        LoginPage(engine).iniciar_sesion(
            mandante=client,
            usuario=user,
            password=password,
            idioma=language,
        )
        return engine

    # ==========================================================
    # EVIDENCIAS VISUALES Y INTEGRACIÓN CON REPORTE LIVERPOOL
    # ==========================================================
    def screenshot_base64(self) -> Optional[str]:
        """Captura la ventana de SAP y la devuelve en Base64 para el reporte HTML."""
        import tempfile
        import base64
        tmp = os.path.join(tempfile.gettempdir(), f"sap_shot_{int(time.time() * 1000)}.png")
        try:
            has_popup = False
            try:
                self.session.findById("wnd[1]")
                has_popup = True
            except Exception:
                has_popup = False

            if has_popup:
                time.sleep(0.3)
                ImageGrab.grab().save(tmp)
            else:
                active = self.session.ActiveWindow
                try:
                    active.HardCopy(tmp, 2)  # 2 = PNG
                except Exception:
                    left, top = active.ScreenLeft, active.ScreenTop
                    ImageGrab.grab(bbox=(left, top, left + active.Width, top + active.Height)).save(tmp)
        except Exception:
            ImageGrab.grab().save(tmp)
        try:
            with open(tmp, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception as e:
            logger.error(f"[-] No se pudo leer la captura: {e}")
            return None
        finally:
            try:
                os.remove(tmp)
            except Exception:
                pass

    def step(self, message: str, status: str = "passed", control=None):
        """Registra un paso en el reporte HTML interactivo, con resaltado y captura opcional."""
        try:
            from utils.report_template import add_step
            from config.settings import Config
            shot = None
            if getattr(Config, "STEP_SCREENSHOTS", True):
                highlighted = False
                if control is not None and getattr(Config, "HIGHLIGHT_FIELDS", True):
                    try:
                        control.Visualize(True)
                        highlighted = True
                        time.sleep(0.2)
                    except Exception:
                        pass
                shot = self.screenshot_base64()
                if highlighted:
                    try:
                        control.Visualize(False)
                    except Exception:
                        pass
            add_step(message, status, shot)
        except Exception:
            logger.info(f"STEP: {message}")

    def _try_get_control(self, element_id: str):
        """Obtiene la referencia COM del control de forma segura para resaltado visual."""
        try:
            return self.session.findById(element_id)
        except Exception:
            return None

    def take_screenshot(self, step_name: str) -> str:
        """Toma una captura de pantalla de evidencia en disco y la guarda en reports/."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", step_name)
        filepath = os.path.join(self.evidence_dir, f"{timestamp}_{safe_name}.png")
        time.sleep(0.4)
        img = ImageGrab.grab()
        img.save(filepath)
        logger.info(f"[EVIDENCIA] Captura guardada en: {filepath}")
        return filepath

    # ==========================================================
    # NAVEGACIÓN Y BARRA DE HERRAMIENTAS (VÍA SAPGUILIBRARY)
    # ==========================================================
    def start_transaction(self, tcode: str):
        """Ejecuta una transacción o comando en el campo OKCode usando `SapGuiLibrary.run_transaction`."""
        code = tcode if tcode.startswith("/n") or tcode.startswith("/o") or tcode.startswith("=") else f"/n{tcode}"
        logger.info(f"Ejecutando transacción/comando vía SapGuiLibrary: {code}")
        self.sap_lib.run_transaction(code)
        self.step(f"Transacción {code}")

    def press_enter(self, describe: str = "Enter"):
        """Envía VKey 0 (Enter) mediante `SapGuiLibrary.send_vkey`."""
        self.sap_lib.send_vkey(0, window=0)
        self.step(describe)

    def click_save(self, describe: str = "Clic en Guardar / Contabilizar"):
        """Presiona el botón Guardar / Contabilizar (wnd[0]/tbar[0]/btn[11]) vía `SapGuiLibrary.click_element`."""
        btn_id = "wnd[0]/tbar[0]/btn[11]"
        logger.info(f"Haciendo clic en Guardar / Contabilizar ({btn_id})")
        ctrl = self._try_get_control(btn_id)
        self.step(describe, control=ctrl)
        self.sap_lib.click_element(btn_id)

    def send_vkey(self, vkey: Union[int, str], window: Union[int, str] = "wnd[0]", describe: Optional[str] = None):
        """Envía una tecla virtual o combinación de teclas SAP usando `SapGuiLibrary.send_vkey`."""
        win_idx = self._normalize_window_index(window)
        self.sap_lib.send_vkey(vkey, window=win_idx)
        if describe:
            self.step(describe)

    def maximize_window(self, window: Union[int, str] = 0):
        """Maximiza la ventana SAP indicada usando `SapGuiLibrary.maximize_window`."""
        win_idx = self._normalize_window_index(window)
        self.sap_lib.maximize_window(win_idx)

    def close_session(self):
        """
        Cierra la sesión de SAP enviando '/nex' mediante `SapGuiLibrary.run_transaction`.
        Si queda algún diálogo de confirmación, lo acepta para liberar la conexión.
        """
        logger.info("Cerrando sesión de SAP (/nex)...")
        try:
            self.sap_lib.run_transaction("/nex")
            time.sleep(0.5)
        except Exception:
            try:
                self.session.findById("wnd[0]").close()
                self.sap_lib.click_element("wnd[1]/usr/btnSPOP-OPTION1")
            except Exception:
                pass

    # ==========================================================
    # INTERACCIÓN CON CONTROLES (DELEGADO EN SAPGUILIBRARY)
    # ==========================================================
    def set_text(self, field_id: str, value: str, label: str = None):
        """
        Ingresa texto en un campo SAP GUI usando `SapGuiLibrary.input_text`
        y registra el paso con evidencia visual.
        """
        str_val = str(value).strip()
        logger.info(f"Input vía SapGuiLibrary en [{field_id}] = '{str_val}'")
        self.sap_lib.input_text(field_id, str_val)
        ctrl = self._try_get_control(field_id)
        self.step(f"{label or field_id.split('/')[-1]} = '{str_val}'", control=ctrl)

    def set_password(self, field_id: str, password: str, label: str = "Contraseña"):
        """Ingresa una contraseña usando `SapGuiLibrary.input_password` sin exponerla en logs ni reportes."""
        logger.info(f"Input password vía SapGuiLibrary en [{field_id}]")
        self.sap_lib.input_password(field_id, str(password))
        ctrl = self._try_get_control(field_id)
        self.step(f"{label} = '********'", control=ctrl)

    def find_control_by_name_suffix(self, suffix: str, container=None):
        """
        Busca recursivamente en el árbol de la pantalla actual de SAP cualquier control
        cuyo ID o Name termine con `suffix` (ej. 'COBL-KOSTL' o 'BSEG-KOSTL').
        Resuelve el problema de subscreens dinámicos (ej. subBLOCK:SAPLKACB:1001 vs 1006).
        """
        if container is None:
            container = self.session.findById("wnd[0]/usr")

        suffix_upper = suffix.upper()
        try:
            name = getattr(container, "Name", "").upper()
            cid = getattr(container, "Id", "").upper()
            if name == suffix_upper or cid.endswith(suffix_upper):
                return container
        except Exception:
            pass

        try:
            children = getattr(container, "Children", None)
            if children is not None:
                for i in range(children.Count):
                    found = self.find_control_by_name_suffix(suffix, children(i))
                    if found is not None:
                        return found
        except Exception:
            pass

        return None

    def set_text_by_Possible_ids(self, field_ids: List[str], value: str, label: str = None) -> str:
        """
        Intenta escribir usando `SapGuiLibrary.input_text` en el primer ID técnico que exista
        o lo busca dinámicamente en el árbol de SAP por su nombre técnico (ej. 'COBL-KOSTL').
        """
        last_err = None
        for fid in field_ids:
            try:
                self.sap_lib.element_should_be_present(fid)
                self.set_text(fid, value, label)
                return fid
            except Exception as e:
                last_err = e

        for fid in field_ids:
            short_name = fid.split("/")[-1]
            clean_name = re.sub(r"^(ctxt|txt|pwd)", "", short_name)
            for candidate in (short_name, clean_name):
                ctrl = self.find_control_by_name_suffix(candidate)
                if ctrl is not None:
                    relative_id = re.sub(r"^/app/con\[\d+\]/ses\[\d+\]/", "", ctrl.Id)
                    self.set_text(relative_id, value, label)
                    return relative_id

        raise LookupError(f"No se encontró ninguno de los controles {field_ids}. Último error: {last_err}")

    def press_button(self, button_id: str, label: str = None):
        """Presiona un botón, pestaña o ítem de menú usando `SapGuiLibrary.click_element`."""
        logger.info(f"Click vía SapGuiLibrary en [{button_id}]")
        ctrl = self._try_get_control(button_id)
        tooltip = getattr(ctrl, "Tooltip", "") if ctrl is not None else ""
        self.step(f"Clic en {label or tooltip or button_id}", control=ctrl)
        self.sap_lib.click_element(button_id)

    def click_toolbar_button(self, table_id: str, button_id: str, label: str = None):
        """Presiona un botón dentro de la barra de herramientas de un GridView (`SapGuiLibrary.click_toolbar_button`)."""
        logger.info(f"Click toolbar button '{button_id}' en tabla [{table_id}]")
        ctrl = self._try_get_control(table_id)
        self.step(f"Clic en botón de tabla {label or button_id}", control=ctrl)
        self.sap_lib.click_toolbar_button(table_id, button_id)

    def select_checkbox(self, element_id: str, selected: bool = True, label: str = None):
        """Marca o desmarca un checkbox usando `SapGuiLibrary.select_checkbox` / `unselect_checkbox`."""
        if selected:
            self.sap_lib.select_checkbox(element_id)
            accion = "Marcar"
        else:
            self.sap_lib.unselect_checkbox(element_id)
            accion = "Desmarcar"
        ctrl = self._try_get_control(element_id)
        self.step(f"{accion} checkbox {label or element_id}", control=ctrl)

    def select_radio_button(self, element_id: str, label: str = None):
        """Selecciona un botón de opción (radio button) usando `SapGuiLibrary.select_radio_button`."""
        self.sap_lib.select_radio_button(element_id)
        ctrl = self._try_get_control(element_id)
        self.step(f"Seleccionar opción {label or element_id}", control=ctrl)

    def select_from_list_by_label(self, element_id: str, value: str, label: str = None):
        """Selecciona una opción de un ComboBox por su etiqueta usando `SapGuiLibrary.select_from_list_by_label`."""
        self.sap_lib.select_from_list_by_label(element_id, value)
        ctrl = self._try_get_control(element_id)
        self.step(f"{label or element_id} = '{value}'", control=ctrl)

    def get_value(self, element_id: str) -> str:
        """Obtiene el valor actual de un control SAP usando `SapGuiLibrary.get_value`."""
        return self.sap_lib.get_value(element_id)

    def get_window_title(self, window: Union[int, str] = "wnd[0]") -> str:
        """Obtiene el título de la ventana SAP usando `SapGuiLibrary.get_window_title`."""
        win_id = self._normalize_window_id(window)
        return self.sap_lib.get_window_title(win_id)

    def element_should_be_present(self, element_id: str, message: Optional[str] = None):
        """Verifica que el control exista en la pantalla actual usando `SapGuiLibrary.element_should_be_present`."""
        self.sap_lib.element_should_be_present(element_id, message=message)

    def element_value_should_be(self, element_id: str, expected_value: str, message: Optional[str] = None):
        """Valida el valor exacto de un control usando `SapGuiLibrary.element_value_should_be`."""
        self.sap_lib.element_value_should_be(element_id, expected_value, message=message)

    def element_value_should_contain(self, element_id: str, expected_value: str, message: Optional[str] = None):
        """Valida que el valor de un control contenga un texto usando `SapGuiLibrary.element_value_should_contain`."""
        self.sap_lib.element_value_should_contain(element_id, expected_value, message=message)

    def get_cell_value(self, table_id: str, row_num: int, col_id: str) -> str:
        """Obtiene el valor de una celda en un GridView usando `SapGuiLibrary.get_cell_value`."""
        return self.sap_lib.get_cell_value(table_id, row_num, col_id)

    def set_cell_value(self, table_id: str, row_num: int, col_id: str, text: str, label: str = None):
        """Escribe un valor en una celda de un GridView usando `SapGuiLibrary.set_cell_value`."""
        self.sap_lib.set_cell_value(table_id, row_num, col_id, text)
        ctrl = self._try_get_control(table_id)
        self.step(f"{label or f'{col_id}[{row_num}]'} = '{text}'", control=ctrl)

    def select_table_row(self, table_id: str, row_num: int, label: str = None):
        """Selecciona una fila de una tabla o GridView usando `SapGuiLibrary.select_table_row`."""
        self.sap_lib.select_table_row(table_id, row_num)
        ctrl = self._try_get_control(table_id)
        self.step(f"Seleccionar fila {row_num} en {label or table_id}", control=ctrl)

    def get_row_count(self, table_id: str) -> int:
        """Devuelve la cantidad de filas en una tabla usando `SapGuiLibrary.get_row_count`."""
        return self.sap_lib.get_row_count(table_id)

    # ==========================================================
    # NAVEGACIÓN DE MENÚ SUPERIOR DE SAP GUI
    # ==========================================================
    def select_menu_by_id(self, menu_id: str, label: str = None):
        """Selecciona un MenuItem usando `SapGuiLibrary.click_element` (que invoca .select() para GuiMenu)."""
        logger.info(f"Seleccionando menú por ID vía SapGuiLibrary: [{menu_id}]")
        self.sap_lib.click_element(menu_id)
        self.step(f"Menú: {label or menu_id}")

    def select_menu_by_path(self, menu_path: str):
        """
        Navega por el menú superior usando los textos visibles separados por '->'.
        Ejemplo: 'Documento->Visualizar' o 'Entorno->Entorno de documento->Documentos financieros'
        """
        parts = [p.strip() for p in menu_path.split("->")]
        logger.info(f"Seleccionando ruta de menú SAP: {' -> '.join(parts)}")
        current_container = self.session.findById("wnd[0]/mbar")

        for part in parts:
            found = False
            for i in range(current_container.Children.Count):
                item = current_container.Children(i)
                clean_text = item.Text.replace("&", "").strip()
                if clean_text.lower() == part.lower() or part.lower() in clean_text.lower():
                    if part == parts[-1]:
                        # Usar SapGuiLibrary.click_element sobre el ID relativo del GuiMenu
                        relative_id = re.sub(r"^/app/con\[\d+\]/ses\[\d+\]/", "", item.Id)
                        self.sap_lib.click_element(relative_id)
                        self.step(f"Menú: {' -> '.join(parts)}")
                    else:
                        current_container = item
                    found = True
                    break
            if not found:
                raise LookupError(f"No se encontró la opción de menú '{part}' dentro de la ruta '{menu_path}'")

    # ==========================================================
    # BARRA DE ESTADO (STATUSBAR) Y BUFFERS
    # ==========================================================
    def get_statusbar_info(self) -> Dict[str, str]:
        """Lee el mensaje completo y los parámetros (Parameter 1..8) de la barra de estado inferior."""
        sbar = self.session.findById("wnd[0]/sbar")
        text = self.sap_lib.get_value("wnd[0]/sbar") or sbar.Text
        info = {
            "text": text,
            "type": sbar.MessageType,  # S=Success, W=Warning, E=Error, I=Info
            "id": sbar.MessageId,
            "number": sbar.MessageNumber,
            "parameter_1": getattr(sbar, "MessageParameter", lambda idx: "")(0) if hasattr(sbar, "MessageParameter") else "",
        }
        if not info["parameter_1"]:
            match = re.search(r"\b(\d{5,12})\b", info["text"])
            if match:
                info["parameter_1"] = match.group(1)
        logger.info(f"Statusbar capturada: [{info['type']}] '{info['text']}' (Param1={info['parameter_1']})")
        return info

    def buffer_statusbar_doc_number(
        self,
        buffer_name: str = "NumDocContable",
        expected_text_contains: str = "se contabilizó",
    ) -> str:
        """
        Verifica el mensaje de la barra inferior y guarda el número de documento en un Buffer
        (Equivalente a {XB[NumDocContable]} en Tosca).
        """
        sbar_info = self.get_statusbar_info()
        if expected_text_contains and expected_text_contains.lower() not in sbar_info["text"].lower():
            raise AssertionError(
                f"El mensaje de la barra de estado '{sbar_info['text']}' no contiene '{expected_text_contains}'"
            )
        doc_num = sbar_info["parameter_1"]
        self.set_buffer(buffer_name, doc_num)
        self.set_buffer(f"{buffer_name}_MensajeCompleto", sbar_info["text"])
        self.step(f"Documento contabilizado: {doc_num} ({sbar_info['text']})")
        return doc_num

    def set_buffer(self, name: str, value: str):
        """Guarda un valor en el diccionario de Buffers y lo imprime en consola/log."""
        self.buffers[name] = str(value)
        logger.info(f"[BUFFER GUARDADO] {name} = '{value}'")

    def get_buffer(self, name: str) -> str:
        """Recupera el valor de un Buffer previamente guardado."""
        if name not in self.buffers:
            raise KeyError(f"El Buffer '{name}' no existe. Buffers actuales: {self.buffers}")
        return self.buffers[name]

    # ==========================================================
    # EXTRACCIÓN DE POP-UPS MODAL EN FINANZAS
    # ==========================================================
    def extract_popup_documents_list(self, window_id: str = "wnd[1]") -> List[Dict[str, str]]:
        """
        Recorre el pop-up 'Lista de documentos en Finanzas' (wnd[1]/usr/lbl...)
        y extrae las filas de 'Nº documento' y 'Texto tipo objeto'.
        """
        win_id = self._normalize_window_id(window_id)
        usr_area = self.session.findById(f"{win_id}/usr")
        items_by_row: Dict[int, List[str]] = {}

        for i in range(usr_area.Children.Count):
            child = usr_area.Children(i)
            text = getattr(child, "Text", "").strip()
            top = getattr(child, "CharTop", i)
            if text:
                items_by_row.setdefault(top, []).append(text)

        extracted = []
        for row_idx in sorted(items_by_row.keys()):
            row_values = items_by_row[row_idx]
            if len(row_values) >= 2 and row_values[0] not in ("Nº documento", "Documentos en Finanzas"):
                doc_no, doc_type = row_values[0], row_values[1]
                extracted.append({"num_documento": doc_no, "tipo_objeto": doc_type})
                self.set_buffer(f"Doc_{doc_type.replace(' ', '_').replace('.', '')}", doc_no)

        logger.info(f"Documentos financieros extraídos del pop-up: {extracted}")
        self.step(f"Pop-up Finanzas: {len(extracted)} documento(s) extraído(s)")
        return extracted
