"""Acceso a datos de vehículos."""

from db import BaseDatos
from modelos.estados import EstadoVehiculo
from modelos.vehiculo import Vehiculo


class RepositorioVehiculos:
    """Operaciones SQL sobre la tabla ``vehiculos``."""

    def __init__(self, base_datos: BaseDatos) -> None:
        self._base_datos = base_datos

    def crear(self, vehiculo: Vehiculo) -> int:
        """Inserta un vehículo y devuelve su identificador."""
        return self._base_datos.ejecutar(
            """
            INSERT INTO vehiculos (
                patente, marca, modelo, anio, categoria, tarifa_diaria, estado
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                vehiculo.patente,
                vehiculo.marca,
                vehiculo.modelo,
                vehiculo.anio,
                vehiculo.categoria,
                vehiculo.tarifa_diaria,
                vehiculo.estado.value,
            ),
        )

    def obtener_por_id(self, vehiculo_id: int) -> Vehiculo | None:
        """Busca un vehículo por su identificador."""
        fila = self._base_datos.consultar_uno(
            """
            SELECT id, patente, marca, modelo, anio, categoria, tarifa_diaria, estado
            FROM vehiculos
            WHERE id = %s
            """,
            (vehiculo_id,),
        )
        return self._desde_fila(fila) if fila is not None else None

    def obtener_por_patente(self, patente: str) -> Vehiculo | None:
        """Busca un vehículo por su patente."""
        fila = self._base_datos.consultar_uno(
            """
            SELECT id, patente, marca, modelo, anio, categoria, tarifa_diaria, estado
            FROM vehiculos
            WHERE patente = %s
            """,
            (patente,),
        )
        return self._desde_fila(fila) if fila is not None else None

    def listar(self, incluir_baja: bool = False) -> list[Vehiculo]:
        """Lista vehículos, excluyendo los dados de baja por defecto."""
        if incluir_baja:
            filas = self._base_datos.consultar_todos(
                """
                SELECT id, patente, marca, modelo, anio, categoria, tarifa_diaria, estado
                FROM vehiculos
                ORDER BY patente
                """
            )
        else:
            filas = self._base_datos.consultar_todos(
                """
                SELECT id, patente, marca, modelo, anio, categoria, tarifa_diaria, estado
                FROM vehiculos
                WHERE estado <> %s
                ORDER BY patente
                """,
                (EstadoVehiculo.BAJA.value,),
            )
        return [self._desde_fila(fila) for fila in filas]

    def actualizar(self, vehiculo: Vehiculo) -> None:
        """Actualiza los datos modificables de un vehículo."""
        if vehiculo.id is None:
            raise ValueError("El vehículo debe tener un id para actualizarse.")

        self._base_datos.ejecutar(
            """
            UPDATE vehiculos
            SET patente = %s,
                marca = %s,
                modelo = %s,
                anio = %s,
                categoria = %s,
                tarifa_diaria = %s
            WHERE id = %s
            """,
            (
                vehiculo.patente,
                vehiculo.marca,
                vehiculo.modelo,
                vehiculo.anio,
                vehiculo.categoria,
                vehiculo.tarifa_diaria,
                vehiculo.id,
            ),
        )

    def actualizar_estado(
        self, vehiculo_id: int, estado: EstadoVehiculo
    ) -> None:
        """Actualiza únicamente el estado operativo del vehículo."""
        self._base_datos.ejecutar(
            "UPDATE vehiculos SET estado = %s WHERE id = %s",
            (estado.value, vehiculo_id),
        )

    @staticmethod
    def _desde_fila(fila: dict) -> Vehiculo:
        return Vehiculo(
            id=fila["id"],
            patente=fila["patente"],
            marca=fila["marca"],
            modelo=fila["modelo"],
            anio=fila["anio"],
            categoria=fila["categoria"],
            tarifa_diaria=fila["tarifa_diaria"],
            estado=EstadoVehiculo(fila["estado"]),
        )
