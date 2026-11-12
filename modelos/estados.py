"""Estados y clasificaciones del dominio."""

from enum import Enum


class EstadoVehiculo(str, Enum):
    """Estado operativo de un vehículo."""

    DISPONIBLE = "disponible"
    ALQUILADO = "alquilado"
    MANTENIMIENTO = "mantenimiento"
    BAJA = "baja"


class EstadoReserva(str, Enum):
    """Estado de una reserva."""

    CONFIRMADA = "confirmada"
    CANCELADA = "cancelada"
    COMPLETADA = "completada"


class EstadoAlquiler(str, Enum):
    """Estado de un alquiler."""

    EN_CURSO = "en_curso"
    FINALIZADO = "finalizado"


class TipoDevolucion(str, Enum):
    """Clasificación de la devolución respecto de la fecha prevista."""

    ANTICIPADA = "anticipada"
    PUNTUAL = "puntual"
    TARDIA = "tardia"
