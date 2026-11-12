"""Pruebas de integración de la conexión y las transacciones."""

from uuid import uuid4

import pytest

from utilidades.excepciones import ErrorBaseDatos, ErrorDuplicado

pytestmark = pytest.mark.integracion


def _nombres_de_tablas(base_datos) -> set[str]:
    filas = base_datos.consultar_todos("SHOW TABLES")
    return {next(iter(fila.values())) for fila in filas}


def test_esquema_contiene_las_cuatro_tablas(base_datos_prueba) -> None:
    assert {"vehiculos", "clientes", "reservas", "alquileres"} <= _nombres_de_tablas(
        base_datos_prueba
    )


def test_commit_y_limpieza_de_cliente(base_datos_prueba) -> None:
    documento = f"T{uuid4().hex[:15]}"

    with base_datos_prueba.transaccion():
        cliente_id = base_datos_prueba.ejecutar(
            """
            INSERT INTO clientes (documento, nombre, apellido)
            VALUES (%s, %s, %s)
            """,
            (documento, "Prueba", "Commit"),
        )

    guardado = base_datos_prueba.consultar_uno(
        "SELECT id, documento FROM clientes WHERE id = %s",
        (cliente_id,),
    )
    assert guardado is not None
    assert guardado["documento"] == documento

    with base_datos_prueba.transaccion():
        base_datos_prueba.ejecutar(
            "DELETE FROM clientes WHERE id = %s",
            (cliente_id,),
        )

    assert (
        base_datos_prueba.consultar_uno(
            "SELECT id FROM clientes WHERE id = %s",
            (cliente_id,),
        )
        is None
    )


def test_rollback_descarta_la_operacion(base_datos_prueba) -> None:
    documento = f"R{uuid4().hex[:15]}"

    with pytest.raises(RuntimeError):
        with base_datos_prueba.transaccion():
            base_datos_prueba.ejecutar(
                """
                INSERT INTO clientes (documento, nombre, apellido)
                VALUES (%s, %s, %s)
                """,
                (documento, "Prueba", "Rollback"),
            )
            raise RuntimeError("Fallo simulado para forzar rollback")

    assert (
        base_datos_prueba.consultar_uno(
            "SELECT id FROM clientes WHERE documento = %s",
            (documento,),
        )
        is None
    )


def test_error_sql_se_encapsula(base_datos_prueba) -> None:
    with pytest.raises(ErrorBaseDatos):
        base_datos_prueba.consultar_todos("SELECT * FROM tabla_inexistente")


def test_patente_unica_se_traduce_en_error_duplicado(base_datos_prueba) -> None:
    patente = f"U{uuid4().hex[:8].upper()}"
    parametros = (patente, "Toyota", "Corolla", 2024, "sedan", "50000.00")

    with base_datos_prueba.transaccion():
        base_datos_prueba.ejecutar(
            """
            INSERT INTO vehiculos (
                patente, marca, modelo, anio, categoria, tarifa_diaria
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            parametros,
        )

    try:
        with pytest.raises(ErrorDuplicado):
            with base_datos_prueba.transaccion():
                base_datos_prueba.ejecutar(
                    """
                    INSERT INTO vehiculos (
                        patente, marca, modelo, anio, categoria, tarifa_diaria
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    parametros,
                )
    finally:
        with base_datos_prueba.transaccion():
            base_datos_prueba.ejecutar(
                "DELETE FROM vehiculos WHERE patente = %s",
                (patente,),
            )
