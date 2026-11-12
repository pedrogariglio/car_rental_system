"""Modelo de alquiler."""

from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from modelos.estados import EstadoAlquiler
from utilidades.excepciones import ErrorValidacion
from utilidades.validaciones import (
    a_decimal,
    validar_entero_positivo,
    validar_enum,
    validar_fecha_hora,
    validar_rango_fechas,
)

CENTIMOS = Decimal("0.01")


@dataclass
class Alquiler:
    """Alquiler originado en una reserva."""

    reserva_id: int
    fecha_hora_retiro_real: datetime
    fecha_hora_devolucion_real: datetime | None = None
    importe_base: Decimal | None = None
    recargo_demora: Decimal = Decimal("0.00")
    importe_final: Decimal | None = None
    estado: EstadoAlquiler = EstadoAlquiler.EN_CURSO
    id: int | None = None

    def __post_init__(self) -> None:
        self.reserva_id = validar_entero_positivo(self.reserva_id, "reserva_id")
        self.fecha_hora_retiro_real = validar_fecha_hora(
            self.fecha_hora_retiro_real, "fecha_hora_retiro_real"
        )
        self.estado = validar_enum(self.estado, EstadoAlquiler, "estado")
        self.recargo_demora = a_decimal(
            self.recargo_demora, "recargo_demora", no_negativo=True
        ).quantize(CENTIMOS, rounding=ROUND_HALF_UP)

        if self.fecha_hora_devolucion_real is not None:
            validar_rango_fechas(
                self.fecha_hora_retiro_real,
                self.fecha_hora_devolucion_real,
                nombre_inicio="fecha_hora_retiro_real",
                nombre_fin="fecha_hora_devolucion_real",
            )

        if self.importe_base is not None:
            self.importe_base = a_decimal(
                self.importe_base, "importe_base", no_negativo=True
            ).quantize(CENTIMOS, rounding=ROUND_HALF_UP)

        if self.importe_final is not None:
            self.importe_final = a_decimal(
                self.importe_final, "importe_final", no_negativo=True
            ).quantize(CENTIMOS, rounding=ROUND_HALF_UP)

        self._validar_estado()
        self._validar_importes()

        if self.id is not None:
            self.id = validar_entero_positivo(self.id, "id")

    def _validar_estado(self) -> None:
        if self.estado is EstadoAlquiler.EN_CURSO:
            if self.fecha_hora_devolucion_real is not None:
                raise ErrorValidacion(
                    "Un alquiler en curso no puede tener devolución real."
                )
            if self.importe_base is not None or self.importe_final is not None:
                raise ErrorValidacion(
                    "Un alquiler en curso no puede tener importes de cierre."
                )
            if self.recargo_demora != Decimal("0.00"):
                raise ErrorValidacion(
                    "Un alquiler en curso no puede tener recargo por demora."
                )
            return

        if self.fecha_hora_devolucion_real is None:
            raise ErrorValidacion(
                "Un alquiler finalizado debe tener devolución real."
            )
        if self.importe_base is None or self.importe_final is None:
            raise ErrorValidacion(
                "Un alquiler finalizado debe tener importe base e importe final."
            )

    def _validar_importes(self) -> None:
        if self.importe_base is None or self.importe_final is None:
            return

        if self.importe_final != self.importe_base + self.recargo_demora:
            raise ErrorValidacion(
                "El importe final debe ser igual al importe base más el recargo."
            )
