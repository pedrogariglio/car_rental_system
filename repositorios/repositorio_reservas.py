"""Acceso a datos de reservas."""

from datetime import datetime

from db import BaseDatos
from modelos.estados import EstadoReserva
from modelos.reserva import Reserva


class RepositorioReservas:
    """Operaciones SQL sobre la tabla ``reservas``."""

    def __init__(self, base_datos: BaseDatos) -> None:
        self._base_datos = base_datos

    def crear(self, reserva: Reserva) -> int:
        """Inserta una reserva y devuelve su identificador."""
        return self._base_datos.ejecutar(
            """
            INSERT INTO reservas (
                cliente_id,
                vehiculo_id,
                fecha_hora_retiro_prevista,
                fecha_hora_devolucion_prevista,
                tarifa_diaria_acordada,
                importe_estimado,
                estado,
                fecha_creacion
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                reserva.cliente_id,
                reserva.vehiculo_id,
                reserva.fecha_hora_retiro_prevista,
                reserva.fecha_hora_devolucion_prevista,
                reserva.tarifa_diaria_acordada,
                reserva.importe_estimado,
                reserva.estado.value,
                reserva.fecha_creacion,
            ),
        )

    def obtener_por_id(
        self, reserva_id: int, *, for_update: bool = False
    ) -> Reserva | None:
        """Busca una reserva por id, opcionalmente bloqueando la fila."""
        sql = """
            SELECT id, cliente_id, vehiculo_id, fecha_hora_retiro_prevista,
                   fecha_hora_devolucion_prevista, tarifa_diaria_acordada,
                   importe_estimado, estado, fecha_creacion
            FROM reservas
            WHERE id = %s
        """
        if for_update:
            sql += " FOR UPDATE"

        fila = self._base_datos.consultar_uno(sql, (reserva_id,))
        return self._desde_fila(fila) if fila is not None else None

    def listar(
        self,
        cliente_id: int | None = None,
        vehiculo_id: int | None = None,
    ) -> list[Reserva]:
        """Lista reservas con filtros opcionales por cliente y vehículo."""
        condiciones: list[str] = []
        parametros: list = []

        if cliente_id is not None:
            condiciones.append("cliente_id = %s")
            parametros.append(cliente_id)
        if vehiculo_id is not None:
            condiciones.append("vehiculo_id = %s")
            parametros.append(vehiculo_id)

        sql = """
            SELECT id, cliente_id, vehiculo_id, fecha_hora_retiro_prevista,
                   fecha_hora_devolucion_prevista, tarifa_diaria_acordada,
                   importe_estimado, estado, fecha_creacion
            FROM reservas
        """
        if condiciones:
            sql += " WHERE " + " AND ".join(condiciones)
        sql += " ORDER BY fecha_hora_retiro_prevista DESC"

        filas = self._base_datos.consultar_todos(sql, parametros)
        return [self._desde_fila(fila) for fila in filas]

    def buscar_solapadas(
        self,
        vehiculo_id: int,
        fecha_hora_retiro: datetime,
        fecha_hora_devolucion: datetime,
        excluir_reserva_id: int | None = None,
        *,
        for_update: bool = True,
    ) -> list[Reserva]:
        """Busca reservas confirmadas que se solapen con el intervalo dado.

        Por defecto bloquea las filas hasta el fin de la transacción.
        """
        condiciones = [
            "vehiculo_id = %s",
            "estado = %s",
            "fecha_hora_retiro_prevista < %s",
            "fecha_hora_devolucion_prevista > %s",
        ]
        parametros: list = [
            vehiculo_id,
            EstadoReserva.CONFIRMADA.value,
            fecha_hora_devolucion,
            fecha_hora_retiro,
        ]

        if excluir_reserva_id is not None:
            condiciones.append("id <> %s")
            parametros.append(excluir_reserva_id)

        sql = """
            SELECT id, cliente_id, vehiculo_id, fecha_hora_retiro_prevista,
                   fecha_hora_devolucion_prevista, tarifa_diaria_acordada,
                   importe_estimado, estado, fecha_creacion
            FROM reservas
            WHERE {condiciones}
        """.format(condiciones=" AND ".join(condiciones))
        if for_update:
            sql += " FOR UPDATE"

        filas = self._base_datos.consultar_todos(sql, parametros)
        return [self._desde_fila(fila) for fila in filas]

    def actualizar(self, reserva: Reserva) -> None:
        """Actualiza fechas, tarifa e importe estimado de una reserva."""
        if reserva.id is None:
            raise ValueError("La reserva debe tener un id para actualizarse.")

        self._base_datos.ejecutar(
            """
            UPDATE reservas
            SET fecha_hora_retiro_prevista = %s,
                fecha_hora_devolucion_prevista = %s,
                tarifa_diaria_acordada = %s,
                importe_estimado = %s
            WHERE id = %s
            """,
            (
                reserva.fecha_hora_retiro_prevista,
                reserva.fecha_hora_devolucion_prevista,
                reserva.tarifa_diaria_acordada,
                reserva.importe_estimado,
                reserva.id,
            ),
        )

    def actualizar_estado(
        self, reserva_id: int, estado: EstadoReserva
    ) -> None:
        """Actualiza únicamente el estado de la reserva."""
        self._base_datos.ejecutar(
            "UPDATE reservas SET estado = %s WHERE id = %s",
            (estado.value, reserva_id),
        )

    @staticmethod
    def _desde_fila(fila: dict) -> Reserva:
        return Reserva(
            id=fila["id"],
            cliente_id=fila["cliente_id"],
            vehiculo_id=fila["vehiculo_id"],
            fecha_hora_retiro_prevista=fila["fecha_hora_retiro_prevista"],
            fecha_hora_devolucion_prevista=fila[
                "fecha_hora_devolucion_prevista"
            ],
            tarifa_diaria_acordada=fila["tarifa_diaria_acordada"],
            importe_estimado=fila["importe_estimado"],
            estado=EstadoReserva(fila["estado"]),
            fecha_creacion=fila["fecha_creacion"],
        )
