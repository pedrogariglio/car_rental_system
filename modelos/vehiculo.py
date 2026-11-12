"""Modelo de vehículo."""

from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from modelos.estados import EstadoVehiculo
from utilidades.excepciones import ErrorValidacion
from utilidades.validaciones import (
    a_decimal,
    validar_entero_positivo,
    validar_enum,
    validar_texto,
)

CENTIMOS = Decimal("0.01")


@dataclass
class Vehiculo:
    """Vehículo registrado en el sistema."""

    patente: str
    marca: str
    modelo: str
    anio: int
    categoria: str
    tarifa_diaria: Decimal
    estado: EstadoVehiculo = EstadoVehiculo.DISPONIBLE
    id: int | None = None

    def __post_init__(self) -> None:
        self.patente = validar_texto(self.patente, "patente").upper()
        self.marca = validar_texto(self.marca, "marca")
        self.modelo = validar_texto(self.modelo, "modelo")
        self.categoria = validar_texto(self.categoria, "categoria")
        self.anio = validar_entero_positivo(self.anio, "año")

        if self.anio < 1900 or self.anio > datetime.now().year + 1:
            raise ErrorValidacion("El año del vehículo no es válido.")

        self.tarifa_diaria = a_decimal(
            self.tarifa_diaria, "tarifa_diaria", positivo=True
        ).quantize(CENTIMOS, rounding=ROUND_HALF_UP)
        self.estado = validar_enum(self.estado, EstadoVehiculo, "estado")

        if self.id is not None:
            self.id = validar_entero_positivo(self.id, "id")
