"""Pruebas de integración del servicio de clientes."""

from uuid import uuid4

import pytest

from servicios.servicio_clientes import ServicioClientes
from utilidades.excepciones import ErrorNoEncontrado, ErrorValidacion

pytestmark = pytest.mark.integracion


def _documento() -> str:
    return f"T{uuid4().hex[:10]}"


def _registrar(
    servicio: ServicioClientes, documento: str | None = None
):
    return servicio.registrar(
        documento or _documento(),
        "Ana",
        "Pérez",
        telefono="3511234567",
        correo_electronico="ana@example.com",
    )


def _eliminar(base_datos, cliente_id: int | None) -> None:
    if cliente_id is None:
        return
    with base_datos.transaccion():
        base_datos.ejecutar(
            "DELETE FROM clientes WHERE id = %s",
            (cliente_id,),
        )


def test_registro_consulta_modificacion_y_baja(base_datos_prueba) -> None:
    servicio = ServicioClientes(base_datos_prueba)
    cliente = _registrar(servicio)

    try:
        assert cliente.id is not None
        assert cliente.activo is True

        recuperado = servicio.obtener(cliente.id)
        assert recuperado.documento == cliente.documento
        assert recuperado.correo_electronico == "ana@example.com"

        modificado = servicio.modificar(
            cliente.id,
            nombre="Ana María",
            telefono=None,
        )
        assert modificado.nombre == "Ana María"
        assert modificado.telefono is None

        dado_de_baja = servicio.dar_de_baja(cliente.id)
        assert dado_de_baja.activo is False
        assert all(c.id != cliente.id for c in servicio.listar())
        assert any(
            c.id == cliente.id for c in servicio.listar(incluir_inactivos=True)
        )

        reactivado = servicio.reactivar(cliente.id)
        assert reactivado.activo is True
    finally:
        _eliminar(base_datos_prueba, cliente.id)


def test_documento_duplicado(base_datos_prueba) -> None:
    servicio = ServicioClientes(base_datos_prueba)
    cliente = _registrar(servicio)

    try:
        with pytest.raises(ErrorValidacion):
            _registrar(servicio, cliente.documento)
    finally:
        _eliminar(base_datos_prueba, cliente.id)


def test_modificar_no_permite_documento_duplicado(base_datos_prueba) -> None:
    servicio = ServicioClientes(base_datos_prueba)
    primero = _registrar(servicio)
    segundo = _registrar(servicio)

    try:
        with pytest.raises(ErrorValidacion):
            servicio.modificar(segundo.id, documento=primero.documento)
    finally:
        _eliminar(base_datos_prueba, primero.id)
        _eliminar(base_datos_prueba, segundo.id)


def test_cliente_inexistente(base_datos_prueba) -> None:
    servicio = ServicioClientes(base_datos_prueba)

    with pytest.raises(ErrorNoEncontrado):
        servicio.obtener(2_000_000_000)


def test_no_permite_modificar_activo_desde_modificar(base_datos_prueba) -> None:
    servicio = ServicioClientes(base_datos_prueba)
    cliente = _registrar(servicio)

    try:
        with pytest.raises(ErrorValidacion):
            servicio.modificar(cliente.id, activo=False)
    finally:
        _eliminar(base_datos_prueba, cliente.id)
