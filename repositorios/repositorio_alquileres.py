"""Acceso a datos de alquileres."""

from datetime import datetime

from db import BaseDatos
from modelos.estados import EstadoAlquiler


class RepositorioAlquileres:
    """Operaciones SQL necesarias para la disponibilidad y el cierre."""

    def __init__(self, base_datos: BaseDatos) -> None:
        self._base_datos = base_datos

    def existe_para_reserva(
        self, reserva_id: int, *, for_update: bool = False
    ) -> bool:
        """Indica si la reserva ya tiene un alquiler asociado."""
        sql = "SELECT id FROM alquileres WHERE reserva_id = %s"
        if for_update:
            sql += " FOR UPDATE"

        return self._base_datos.consultar_uno(sql, (reserva_id,)) is not None

    def existe_en_curso_solapado(
        self,
        vehiculo_id: int,
        fecha_hora_devolucion: datetime,
        *,
        for_update: bool = False,
    ) -> bool:
        """Indica si un alquiler en curso se solapa con el intervalo solicitado.

        Un alquiler en curso bloquea desde su retiro real y sin fecha de fin.
        """
        sql = """
            SELECT a.id
            FROM alquileres a
            INNER JOIN reservas r ON r.id = a.reserva_id
            WHERE r.vehiculo_id = %s
              AND a.estado = %s
              AND a.fecha_hora_retiro_real < %s
        """
        if for_update:
            sql += " FOR UPDATE"

        fila = self._base_datos.consultar_uno(
            sql,
            (
                vehiculo_id,
                EstadoAlquiler.EN_CURSO.value,
                fecha_hora_devolucion,
            ),
        )
        return fila is not None
