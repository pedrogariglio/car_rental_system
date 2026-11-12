"""Pruebas de integración del servicio de vehículos."""

from decimal import Decimal
from uuid import uuid4

import pytest

from modelos.estados import EstadoVehiculo
from servicios.servicio_vehiculos import ServicioVehiculos
from utilidades.excepciones import ErrorNoEncontrado, ErrorValidacion

pytestmark = pytest.mark.integracion

TARIFA = Decimal("50000.00")


def _patente() -> str:
    return f"T{uuid4().hex[:6].upper()}"


def _registrar(
    servicio: ServicioVehiculos, patente: str | None = None
):
    return servicio.registrar(
        patente or _patente(),
        "Toyota",
        "Corolla",
        2024,
        "sedan",
        TARIFA,
    )


def _eliminar(base_datos, vehiculo_id: int | None) -> None:
    if vehiculo_id is None:
        return
    with base_datos.transaccion():
        base_datos.ejecutar(
            "DELETE FROM vehiculos WHERE id = %s",
            (vehiculo_id,),
        )


def test_registro_consulta_modificacion_y_baja(base_datos_prueba) -> None:
    servicio = ServicioVehiculos(base_datos_prueba)
    patente = _patente()
    vehiculo = _registrar(servicio, patente.lower())

    try:
        assert vehiculo.id is not None
        assert vehiculo.patente == patente.upper()

        recuperado = servicio.obtener(vehiculo.id)
        assert recuperado.tarifa_diaria == TARIFA
        assert recuperado.estado is EstadoVehiculo.DISPONIBLE

        modificado = servicio.modificar(
            vehiculo.id,
            modelo="Corolla Cross",
            tarifa_diaria=Decimal("55000"),
        )
        assert modificado.modelo == "Corolla Cross"
        assert modificado.tarifa_diaria == Decimal("55000.00")

        dado_de_baja = servicio.dar_de_baja(vehiculo.id)
        assert dado_de_baja.estado is EstadoVehiculo.BAJA
        assert all(v.id != vehiculo.id for v in servicio.listar())
        assert any(
            v.id == vehiculo.id for v in servicio.listar(incluir_baja=True)
        )

        reactivado = servicio.cambiar_estado(
            vehiculo.id, EstadoVehiculo.DISPONIBLE
        )
        assert reactivado.estado is EstadoVehiculo.DISPONIBLE
    finally:
        _eliminar(base_datos_prueba, vehiculo.id)


def test_patente_duplicada(base_datos_prueba) -> None:
    servicio = ServicioVehiculos(base_datos_prueba)
    vehiculo = _registrar(servicio)

    try:
        with pytest.raises(ErrorValidacion):
            _registrar(servicio, vehiculo.patente.lower())
    finally:
        _eliminar(base_datos_prueba, vehiculo.id)


def test_modificar_no_permite_patente_duplicada(base_datos_prueba) -> None:
    servicio = ServicioVehiculos(base_datos_prueba)
    primero = _registrar(servicio)
    segundo = _registrar(servicio)

    try:
        with pytest.raises(ErrorValidacion):
            servicio.modificar(segundo.id, patente=primero.patente)
    finally:
        _eliminar(base_datos_prueba, primero.id)
        _eliminar(base_datos_prueba, segundo.id)


def test_vehiculo_inexistente(base_datos_prueba) -> None:
    servicio = ServicioVehiculos(base_datos_prueba)

    with pytest.raises(ErrorNoEncontrado):
        servicio.obtener(2_000_000_000)


def test_no_permite_modificar_estado_desde_modificar(base_datos_prueba) -> None:
    servicio = ServicioVehiculos(base_datos_prueba)
    vehiculo = _registrar(servicio)

    try:
        with pytest.raises(ErrorValidacion):
            servicio.modificar(vehiculo.id, estado=EstadoVehiculo.BAJA)
    finally:
        _eliminar(base_datos_prueba, vehiculo.id)
