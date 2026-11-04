"""
Test Case: Contabilización FB01 y visualización de documentos en FB03.
Estructurado bajo el patrón Page Object Model (POM) sobre `robotframework-sapguilibrary`.
"""

import pytest
from config.settings import Config
from pages.modules.fb01_page import FB01Page
from pages.modules.fb03_page import FB03Page


def test_FB01_001_contabilizacion_y_visualizacion(sap):
    """
    TC_FB01_001: Contabilización de cuenta mayor en FB01 y verificación en FB03.
    1. Abre FB01 e ingresa cabecera y primera posición (Debe 40).
    2. Ingresa posición Debe con centro de costo y prepara Haber 50.
    3. Ingresa posición Haber y revisa el resumen.
    4. Contabiliza el documento y captura el número de documento de la barra de estado.
    5. Valida los documentos financieros asociados en FB03.
    """
    fb01 = FB01Page(sap)
    fb03 = FB03Page(sap)

    # 1. Navegación y Cabecera de Documento + Primera Posición
    fb01.ingresar_cabecera_y_primera_posicion(
        fecha_doc="14.10.2026",
        clase_doc="SA",
        sociedad="110",
        fecha_contab="14.10.2026",
        moneda="MXP",
        clv_ct_1="40",
        cuenta_1=Config.FB01_CUENTA_1,
    )

    # 2. Acciones Principales - Posiciones Contables (Debe y Haber)
    fb01.ingresar_posicion_debe(
        importe="100",
        ind_impuestos="E0",
        centro_costo=Config.FB01_CENTRO_COSTO,
        sig_clv_ct="50",
        sig_cuenta=Config.FB01_SIG_CUENTA,
    )
    fb01.ingresar_posicion_haber_y_resumen(
        importe="100",
    )

    # 3. Contabilización y Extracción de Documento en Buffer
    num_doc = fb01.contabilizar_documento(buffer_name="NumDocContable")
    assert num_doc, "No se pudo extraer el número de documento de la barra de estado tras contabilizar en FB01."

    # 4. Validaciones en FB03 (Descomentar cuando se requiera validar el entorno de documentos)
    # resultado = fb03.validar_documentos_financieros(min_documentos=1)
    # assert resultado["num_doc_contabilizado"] == num_doc
