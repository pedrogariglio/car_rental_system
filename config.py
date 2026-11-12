"""Configuración de la aplicación y de la conexión a MySQL."""

import os
from pathlib import Path

from dotenv import load_dotenv

from utilidades.excepciones import ErrorConfiguracion

RUTA_ENV = Path(__file__).resolve().parent / ".env"

load_dotenv(dotenv_path=RUTA_ENV)


def obtener_config_bd(nombre_base: str | None = None) -> dict:
    """Devuelve la configuración de conexión a MySQL.

    Si no se indica un nombre de base, se usa ``DB_NAME``.
    """
    base = nombre_base or _texto_obligatorio("DB_NAME")
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": _entero_entorno("DB_PORT", 3306),
        "user": _texto_obligatorio("DB_USER"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": base,
    }


def obtener_config_bd_pruebas() -> dict:
    """Devuelve la configuración de la base de datos de pruebas."""
    return obtener_config_bd(_texto_obligatorio("DB_TEST_NAME"))


def _texto_obligatorio(nombre: str) -> str:
    valor = os.getenv(nombre)
    if valor is None or not valor.strip():
        raise ErrorConfiguracion(
            f"Falta la variable de entorno obligatoria {nombre}."
        )
    return valor.strip()


def _entero_entorno(nombre: str, por_defecto: int) -> int:
    valor = os.getenv(nombre, str(por_defecto))
    try:
        return int(valor)
    except ValueError as exc:
        raise ErrorConfiguracion(f"{nombre} debe ser un número entero.") from exc
