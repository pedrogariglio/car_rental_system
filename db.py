"""Conexión y operaciones de bajo nivel contra MySQL con PyMySQL."""

from contextlib import contextmanager
from typing import Iterator

import pymysql
from pymysql.cursors import DictCursor
from pymysql.err import IntegrityError

from utilidades.excepciones import ErrorBaseDatos, ErrorDuplicado


class BaseDatos:
    """Administra una conexión MySQL y sus transacciones."""

    def __init__(self, configuracion: dict) -> None:
        self.configuracion = configuracion
        self.conexion: pymysql.connections.Connection | None = None

    def conectar(self) -> None:
        """Abre la conexión si todavía no está activa."""
        if self.conexion is not None and self.conexion.open:
            return

        try:
            self.conexion = pymysql.connect(
                **self.configuracion,
                charset="utf8mb4",
                cursorclass=DictCursor,
                autocommit=False,
            )
        except pymysql.Error as exc:
            raise _traducir_error(exc, "No se pudo conectar a MySQL") from exc

    def consultar_uno(
        self, sql: str, parametros: tuple | list | None = None
    ) -> dict | None:
        """Ejecuta un SELECT y devuelve la primera fila o None."""
        self._asegurar_conexion()
        cursor = self.conexion.cursor()
        try:
            cursor.execute(sql, parametros or ())
            return cursor.fetchone()
        except pymysql.Error as exc:
            raise _traducir_error(exc, "Error al consultar MySQL") from exc
        finally:
            cursor.close()

    def consultar_todos(
        self, sql: str, parametros: tuple | list | None = None
    ) -> list[dict]:
        """Ejecuta un SELECT y devuelve todas las filas."""
        self._asegurar_conexion()
        cursor = self.conexion.cursor()
        try:
            cursor.execute(sql, parametros or ())
            return list(cursor.fetchall())
        except pymysql.Error as exc:
            raise _traducir_error(exc, "Error al consultar MySQL") from exc
        finally:
            cursor.close()

    def ejecutar(
        self, sql: str, parametros: tuple | list | None = None
    ) -> int:
        """Ejecuta INSERT, UPDATE o DELETE sin confirmar la transacción."""
        self._asegurar_conexion()
        cursor = self.conexion.cursor()
        try:
            cursor.execute(sql, parametros or ())
            return int(cursor.lastrowid or cursor.rowcount)
        except pymysql.Error as exc:
            raise _traducir_error(exc, "Error al ejecutar SQL") from exc
        finally:
            cursor.close()

    def commit(self) -> None:
        """Confirma la transacción actual."""
        self._asegurar_conexion()
        self.conexion.commit()

    def rollback(self) -> None:
        """Revierte la transacción actual."""
        self._asegurar_conexion()
        self.conexion.rollback()

    @contextmanager
    def transaccion(self) -> Iterator["BaseDatos"]:
        """Agrupa operaciones en una transacción con commit o rollback."""
        self._asegurar_conexion()
        try:
            yield self
        except Exception:
            self.conexion.rollback()
            raise
        else:
            self.conexion.commit()

    def cerrar(self) -> None:
        """Cierra la conexión si está abierta."""
        if self.conexion is not None and self.conexion.open:
            self.conexion.close()

    def _asegurar_conexion(self) -> None:
        if self.conexion is None or not self.conexion.open:
            self.conectar()


def _traducir_error(exc: pymysql.Error, mensaje: str) -> ErrorBaseDatos:
    """Convierte un error de PyMySQL en una excepción de la aplicación."""
    if isinstance(exc, IntegrityError) and exc.args and exc.args[0] == 1062:
        return ErrorDuplicado(f"{mensaje}: registro duplicado.")
    return ErrorBaseDatos(f"{mensaje}: {exc}")
