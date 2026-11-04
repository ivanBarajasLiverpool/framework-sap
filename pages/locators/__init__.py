"""
Paquete centralizado de localizadores para la arquitectura POM de SAP GUI.
"""

from pages.locators.common_locators import CommonLocators, LoginLocators
from pages.locators.fb01_locators import FB01Locators
from pages.locators.fb03_locators import FB03Locators

__all__ = [
    "CommonLocators",
    "LoginLocators",
    "FB01Locators",
    "FB03Locators",
]

