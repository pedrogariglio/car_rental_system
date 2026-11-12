"""Acceso a datos de clientes."""

from db import BaseDatos
from modelos.cliente import Cliente


class RepositorioClientes:
    """Operaciones SQL sobre la tabla ``clientes``."""

    def __init__(self, base_datos: BaseDatos) -> None:
        self._base_datos = base_datos

    def crear(self, cliente: Cliente) -> int:
        """Inserta un cliente y devuelve su identificador."""
        return self._base_datos.ejecutar(
            """
            INSERT INTO clientes (
                documento, nombre, apellido, telefono, correo_electronico, activo
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                cliente.documento,
                cliente.nombre,
                cliente.apellido,
                cliente.telefono,
                cliente.correo_electronico,
                int(cliente.activo),
            ),
        )

    def obtener_por_id(self, cliente_id: int) -> Cliente | None:
        """Busca un cliente por su identificador."""
        fila = self._base_datos.consultar_uno(
            """
            SELECT id, documento, nombre, apellido, telefono,
                   correo_electronico, activo
            FROM clientes
            WHERE id = %s
            """,
            (cliente_id,),
        )
        return self._desde_fila(fila) if fila is not None else None

    def obtener_por_documento(self, documento: str) -> Cliente | None:
        """Busca un cliente por su documento."""
        fila = self._base_datos.consultar_uno(
            """
            SELECT id, documento, nombre, apellido, telefono,
                   correo_electronico, activo
            FROM clientes
            WHERE documento = %s
            """,
            (documento,),
        )
        return self._desde_fila(fila) if fila is not None else None

    def listar(self, incluir_inactivos: bool = False) -> list[Cliente]:
        """Lista clientes, excluyendo los inactivos por defecto."""
        if incluir_inactivos:
            filas = self._base_datos.consultar_todos(
                """
                SELECT id, documento, nombre, apellido, telefono,
                       correo_electronico, activo
                FROM clientes
                ORDER BY apellido, nombre
                """
            )
        else:
            filas = self._base_datos.consultar_todos(
                """
                SELECT id, documento, nombre, apellido, telefono,
                       correo_electronico, activo
                FROM clientes
                WHERE activo = 1
                ORDER BY apellido, nombre
                """
            )
        return [self._desde_fila(fila) for fila in filas]

    def actualizar(self, cliente: Cliente) -> None:
        """Actualiza los datos modificables de un cliente."""
        if cliente.id is None:
            raise ValueError("El cliente debe tener un id para actualizarse.")

        self._base_datos.ejecutar(
            """
            UPDATE clientes
            SET documento = %s,
                nombre = %s,
                apellido = %s,
                telefono = %s,
                correo_electronico = %s,
                activo = %s
            WHERE id = %s
            """,
            (
                cliente.documento,
                cliente.nombre,
                cliente.apellido,
                cliente.telefono,
                cliente.correo_electronico,
                int(cliente.activo),
                cliente.id,
            ),
        )

    def actualizar_activo(self, cliente_id: int, activo: bool) -> None:
        """Actualiza únicamente el estado lógico del cliente."""
        self._base_datos.ejecutar(
            "UPDATE clientes SET activo = %s WHERE id = %s",
            (int(activo), cliente_id),
        )

    @staticmethod
    def _desde_fila(fila: dict) -> Cliente:
        return Cliente(
            id=fila["id"],
            documento=fila["documento"],
            nombre=fila["nombre"],
            apellido=fila["apellido"],
            telefono=fila["telefono"],
            correo_electronico=fila["correo_electronico"],
            activo=bool(fila["activo"]),
        )
