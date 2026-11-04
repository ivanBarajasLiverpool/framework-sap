"""
Paquete raíz `pages`: Re-exporta las clases POM de `pages.modules` y los localizadores de `pages.locators`.
"""

from pages.modules import BasePage, LoginPage, FB01Page, FB03Page
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

