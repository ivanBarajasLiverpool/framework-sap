"""
Paquete `pages`: Implementación completa del patrón Page Object Model (POM)
para SAP GUI sobre `robotframework-sapguilibrary`.
"""

from pages.modules.base_page import BasePage
from pages.modules.login_page import LoginPage
from pages.modules.fb01_page import FB01Page
from pages.modules.fb03_page import FB03Page
from pages.locators import CommonLocators, LoginLocators, FB01Locators, FB03Locators

__all__ = [
    "BasePage",
    "LoginPage",
    "FB01Page",
    "FB03Page",
    "CommonLocators",
    "LoginLocators",
    "FB01Locators",
    "FB03Locators",
]

