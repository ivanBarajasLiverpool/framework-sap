"""
Módulo `sap_driver`: Expone `SAPDriver` como alias semántico de `SAPEngine`
para la arquitectura POM basada en `robotframework-sapguilibrary`.
"""

from core.sap_engine import SAPEngine as SAPDriver, SAPEngine

__all__ = ["SAPDriver", "SAPEngine"]

