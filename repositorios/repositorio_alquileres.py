"""Acceso a datos de alquileres."""

from datetime import datetime

from db import BaseDatos
from modelos.alquiler import Alquiler
from modelos.estados import EstadoAlquiler


class RepositorioAlquileres:
    """Operaciones SQL sobre la tabla ``alquileres``."""

    def __init__(self, base_datos: BaseDatos) -> None:
        self._base_datos = base_datos

    def crear(self, alquiler: Alquiler) -> int:
        """Inserta un alquiler en curso y devuelve su identificador."""
        return self._base_datos.ejecutar(
            """
            INSERT INTO alquileres (
                reserva_id,
                fecha_hora_retiro_real,
                recargo_demora,
                estado
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                alquiler.reserva_id,
                alquiler.fecha_hora_retiro_real,
                alquiler.recargo_demora,
                alquiler.estado.value,
            ),
        )

    def obtener_por_id(
        self, alquiler_id: int, *, for_update: bool = False
    ) -> Alquiler | None:
        """Busca un alquiler por id, opcionalmente bloqueando la fila."""
        sql = """
            SELECT id, reserva_id, fecha_hora_retiro_real,
                   fecha_hora_devolucion_real, importe_base, recargo_demora,
                   importe_final, estado
            FROM alquileres
            WHERE id = %s
        """
        if for_update:
            sql += " FOR UPDATE"

        fila = self._base_datos.consultar_uno(sql, (alquiler_id,))
        return self._desde_fila(fila) if fila is not None else None

    def obtener_por_reserva_id(
        self, reserva_id: int, *, for_update: bool = False
    ) -> Alquiler | None:
        """Busca el alquiler asociado a una reserva."""
        sql = """
            SELECT id, reserva_id, fecha_hora_retiro_real,
                   fecha_hora_devolucion_real, importe_base, recargo_demora,
                   importe_final, estado
            FROM alquileres
            WHERE reserva_id = %s
        """
        if for_update:
            sql += " FOR UPDATE"

        fila = self._base_datos.consultar_uno(sql, (reserva_id,))
        return self._desde_fila(fila) if fila is not None else None

    def listar(
        self,
        cliente_id: int | None = None,
        vehiculo_id: int | None = None,
    ) -> list[Alquiler]:
        """Lista alquileres con filtros opcionales por cliente y vehículo."""
        condiciones: list[str] = []
        parametros: list = []

        if cliente_id is not None:
            condiciones.append("r.cliente_id = %s")
            parametros.append(cliente_id)
        if vehiculo_id is not None:
            condiciones.append("r.vehiculo_id = %s")
            parametros.append(vehiculo_id)

        sql = """
            SELECT a.id, a.reserva_id, a.fecha_hora_retiro_real,
                   a.fecha_hora_devolucion_real, a.importe_base,
                   a.recargo_demora, a.importe_final, a.estado
            FROM alquileres a
            INNER JOIN reservas r ON r.id = a.reserva_id
        """
        if condiciones:
            sql += " WHERE " + " AND ".join(condiciones)
        sql += " ORDER BY a.fecha_hora_retiro_real DESC"

        filas = self._base_datos.consultar_todos(sql, parametros)
        return [self._desde_fila(fila) for fila in filas]

    def actualizar_cierre(self, alquiler: Alquiler) -> None:
        """Persiste la devolución y el desglose económico del cierre."""
        if alquiler.id is None:
            raise ValueError("El alquiler debe tener un id para cerrarse.")

        self._base_datos.ejecutar(
            """
            UPDATE alquileres
            SET fecha_hora_devolucion_real = %s,
                importe_base = %s,
                recargo_demora = %s,
                importe_final = %s,
                estado = %s
            WHERE id = %s
            """,
            (
                alquiler.fecha_hora_devolucion_real,
                alquiler.importe_base,
                alquiler.recargo_demora,
                alquiler.importe_final,
                alquiler.estado.value,
                alquiler.id,
            ),
        )

    def existe_para_reserva(
        self, reserva_id: int, *, for_update: bool = False
    ) -> bool:
        """Indica si la reserva ya tiene un alquiler asociado."""
        sql = "SELECT id FROM alquileres WHERE reserva_id = %s"
        if for_update:
            sql += " FOR UPDATE"

        return self._base_datos.consultar_uno(sql, (reserva_id,)) is not None

    def existe_en_curso_para_vehiculo(
        self, vehiculo_id: int, *, for_update: bool = False
    ) -> bool:
        """Indica si el vehículo tiene algún alquiler en curso."""
        sql = """
            SELECT a.id
            FROM alquileres a
            INNER JOIN reservas r ON r.id = a.reserva_id
            WHERE r.vehiculo_id = %s
              AND a.estado = %s
        """
        if for_update:
            sql += " FOR UPDATE"

        fila = self._base_datos.consultar_uno(
            sql,
            (vehiculo_id, EstadoAlquiler.EN_CURSO.value),
        )
        return fila is not None

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

    @staticmethod
    def _desde_fila(fila: dict) -> Alquiler:
        return Alquiler(
            id=fila["id"],
            reserva_id=fila["reserva_id"],
            fecha_hora_retiro_real=fila["fecha_hora_retiro_real"],
            fecha_hora_devolucion_real=fila["fecha_hora_devolucion_real"],
            importe_base=fila["importe_base"],
            recargo_demora=fila["recargo_demora"],
            importe_final=fila["importe_final"],
            estado=EstadoAlquiler(fila["estado"]),
        )
