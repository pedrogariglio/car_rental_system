"""Modelo de reserva."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from modelos.estados import EstadoReserva
from utilidades.validaciones import (
    a_decimal,
    validar_entero_positivo,
    validar_enum,
    validar_fecha_hora,
    validar_rango_fechas,
)

CENTIMOS = Decimal("0.01")


@dataclass
class Reserva:
    """Reserva de un vehículo para un período determinado."""

    cliente_id: int
    vehiculo_id: int
    fecha_hora_retiro_prevista: datetime
    fecha_hora_devolucion_prevista: datetime
    tarifa_diaria_acordada: Decimal
    importe_estimado: Decimal
    estado: EstadoReserva = EstadoReserva.CONFIRMADA
    fecha_creacion: datetime = field(default_factory=datetime.now)
    id: int | None = None

    def __post_init__(self) -> None:
        self.cliente_id = validar_entero_positivo(self.cliente_id, "cliente_id")
        self.vehiculo_id = validar_entero_positivo(self.vehiculo_id, "vehiculo_id")
        (
            self.fecha_hora_retiro_prevista,
            self.fecha_hora_devolucion_prevista,
        ) = validar_rango_fechas(
            self.fecha_hora_retiro_prevista,
            self.fecha_hora_devolucion_prevista,
            nombre_inicio="fecha_hora_retiro_prevista",
            nombre_fin="fecha_hora_devolucion_prevista",
        )
        self.tarifa_diaria_acordada = a_decimal(
            self.tarifa_diaria_acordada, "tarifa_diaria_acordada", positivo=True
        ).quantize(CENTIMOS, rounding=ROUND_HALF_UP)
        self.importe_estimado = a_decimal(
            self.importe_estimado, "importe_estimado", no_negativo=True
        ).quantize(CENTIMOS, rounding=ROUND_HALF_UP)
        self.estado = validar_enum(self.estado, EstadoReserva, "estado")
        self.fecha_creacion = validar_fecha_hora(
            self.fecha_creacion, "fecha_creacion"
        )

        if self.id is not None:
            self.id = validar_entero_positivo(self.id, "id")

    @property
    def bloquea_disponibilidad(self) -> bool:
        """Indica si la reserva bloquea el vehículo en su intervalo previsto."""
        return self.estado is EstadoReserva.CONFIRMADA
