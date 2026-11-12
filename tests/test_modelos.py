"""Pruebas básicas de validación de los modelos de dominio."""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from modelos.alquiler import Alquiler
from modelos.cliente import Cliente
from modelos.estados import EstadoAlquiler, EstadoReserva
from modelos.reserva import Reserva
from modelos.vehiculo import Vehiculo
from utilidades.excepciones import ErrorValidacion

INICIO = datetime(2026, 11, 10, 10, 0)


def test_vehiculo_normaliza_patente_y_tarifa() -> None:
    vehiculo = Vehiculo(
        patente="ab 123 cd",
        marca="Toyota",
        modelo="Corolla",
        anio=2024,
        categoria="sedan",
        tarifa_diaria=Decimal("50000"),
    )

    assert vehiculo.patente == "AB 123 CD"
    assert vehiculo.tarifa_diaria == Decimal("50000.00")


def test_vehiculo_rechaza_float_en_tarifa() -> None:
    with pytest.raises(TypeError):
        Vehiculo(
            patente="AB123CD",
            marca="Toyota",
            modelo="Corolla",
            anio=2024,
            categoria="sedan",
            tarifa_diaria=50000.0,  # type: ignore[arg-type]
        )


def test_cliente_normaliza_campos_opcionales() -> None:
    cliente = Cliente(
        documento="30111222",
        nombre="Ana",
        apellido="Pérez",
        telefono="   ",
        correo_electronico=None,
    )

    assert cliente.telefono is None
    assert cliente.activo is True


def test_reserva_rechaza_rango_invalido() -> None:
    with pytest.raises(ErrorValidacion):
        Reserva(
            cliente_id=1,
            vehiculo_id=1,
            fecha_hora_retiro_prevista=INICIO,
            fecha_hora_devolucion_prevista=INICIO,
            tarifa_diaria_acordada=Decimal("10000.00"),
            importe_estimado=Decimal("10000.00"),
        )


def test_reserva_solo_bloquea_si_esta_confirmada() -> None:
    reserva = Reserva(
        cliente_id=1,
        vehiculo_id=1,
        fecha_hora_retiro_prevista=INICIO,
        fecha_hora_devolucion_prevista=INICIO + timedelta(hours=24),
        tarifa_diaria_acordada=Decimal("10000.00"),
        importe_estimado=Decimal("10000.00"),
    )

    assert reserva.bloquea_disponibilidad is True
    reserva.estado = EstadoReserva.CANCELADA
    assert reserva.bloquea_disponibilidad is False


def test_alquiler_en_curso_no_admite_datos_de_cierre() -> None:
    with pytest.raises(ErrorValidacion):
        Alquiler(
            reserva_id=1,
            fecha_hora_retiro_real=INICIO,
            fecha_hora_devolucion_real=INICIO + timedelta(hours=24),
        )


def test_alquiler_finalizado_valida_invariante_de_importes() -> None:
    alquiler = Alquiler(
        reserva_id=1,
        fecha_hora_retiro_real=INICIO,
        fecha_hora_devolucion_real=INICIO + timedelta(hours=25),
        importe_base=Decimal("1000.00"),
        recargo_demora=Decimal("41.67"),
        importe_final=Decimal("1041.67"),
        estado=EstadoAlquiler.FINALIZADO,
    )

    assert alquiler.importe_final == (
        alquiler.importe_base + alquiler.recargo_demora
    )


def test_alquiler_finalizado_rechaza_inconsistencia() -> None:
    with pytest.raises(ErrorValidacion):
        Alquiler(
            reserva_id=1,
            fecha_hora_retiro_real=INICIO,
            fecha_hora_devolucion_real=INICIO + timedelta(hours=25),
            importe_base=Decimal("1000.00"),
            recargo_demora=Decimal("41.67"),
            importe_final=Decimal("1041.68"),
            estado=EstadoAlquiler.FINALIZADO,
        )
