"""Generic execution guard with append-only evidence ledger."""

from .ledger import Ledger, componente, configurar_ledger, pieza
from .core import (
    ESTADOS,
    evaluar,
    ejecutar_configuracion,
    cargar_configuracion,
)
from .contorno import siguiente_contorno, clasificar_obstaculo

__all__ = [
    "Ledger",
    "componente",
    "configurar_ledger",
    "pieza",
    "ESTADOS",
    "evaluar",
    "ejecutar_configuracion",
    "cargar_configuracion",
    "siguiente_contorno",
    "clasificar_obstaculo",
]
