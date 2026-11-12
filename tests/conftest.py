"""Fixtures compartidos por la suite de pruebas."""

import re
from pathlib import Path

import pymysql
import pytest

from config import obtener_config_bd_pruebas
from db import BaseDatos
from utilidades.excepciones import ErrorBaseDatos, ErrorConfiguracion

RUTA_ESQUEMA = Path(__file__).resolve().parents[1] / "sql" / "schema.sql"


@pytest.fixture(scope="session")
def base_datos_prueba():
    """Prepara la base de pruebas y la deja disponible para la sesión."""
    try:
        configuracion = obtener_config_bd_pruebas()
    except ErrorConfiguracion as exc:
        pytest.skip(f"Configuración de pruebas incompleta: {exc}")

    _crear_base_si_no_existe(configuracion)

    base_datos = BaseDatos(configuracion)
    try:
        base_datos.conectar()
        for sentencia in _sentencias_esquema():
            base_datos.ejecutar(sentencia)
        base_datos.commit()
    except ErrorBaseDatos as exc:
        base_datos.cerrar()
        pytest.skip(f"MySQL no disponible para pruebas de integración: {exc}")

    yield base_datos
    base_datos.cerrar()


def _crear_base_si_no_existe(configuracion: dict) -> None:
    nombre = configuracion["database"]
    if not re.fullmatch(r"[A-Za-z0-9_]+", nombre):
        pytest.skip("DB_TEST_NAME solo puede contener letras, números y guiones bajos.")

    configuracion_servidor = {
        clave: valor
        for clave, valor in configuracion.items()
        if clave != "database"
    }

    try:
        conexion = pymysql.connect(**configuracion_servidor, autocommit=True)
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{nombre}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
        finally:
            conexion.close()
    except pymysql.Error as exc:
        pytest.skip(f"No se pudo preparar la base de pruebas: {exc}")


def _sentencias_esquema():
    contenido = RUTA_ESQUEMA.read_text(encoding="utf-8")
    for sentencia in contenido.split(";"):
        sentencia = sentencia.strip()
        if sentencia:
            yield sentencia
