"""Modelo de cliente."""

from dataclasses import dataclass

from utilidades.validaciones import (
    validar_entero_positivo,
    validar_texto,
    validar_texto_opcional,
)


@dataclass
class Cliente:
    """Cliente que puede generar reservas y alquileres."""

    documento: str
    nombre: str
    apellido: str
    telefono: str | None = None
    correo_electronico: str | None = None
    activo: bool = True
    id: int | None = None

    def __post_init__(self) -> None:
        self.documento = validar_texto(self.documento, "documento")
        self.nombre = validar_texto(self.nombre, "nombre")
        self.apellido = validar_texto(self.apellido, "apellido")
        self.telefono = validar_texto_opcional(self.telefono, "telefono")
        self.correo_electronico = validar_texto_opcional(
            self.correo_electronico, "correo_electronico"
        )

        if not isinstance(self.activo, bool):
            raise TypeError("activo debe ser booleano.")

        if self.id is not None:
            self.id = validar_entero_positivo(self.id, "id")
