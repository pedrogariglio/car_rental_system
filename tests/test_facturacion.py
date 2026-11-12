"""Pruebas de la política de facturación (casos F-01 a F-14)."""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from modelos.estados import TipoDevolucion
from servicios.facturacion import (
    calcular_bloques_24h,
    calcular_facturacion,
    calcular_importe_estimado,
)
from utilidades.excepciones import ErrorValidacion

TARIFA = Decimal("10000.00")
INICIO = datetime(2026, 11, 10, 10, 0)


def _facturar(
    horas_contratadas: int,
    horas_reales: int,
    *,
    tarifa: Decimal = TARIFA,
    minutos_reales: int = 0,
    minutos_contratados: int = 0,
):
    return calcular_facturacion(
        tarifa,
        INICIO,
        INICIO + timedelta(hours=horas_contratadas, minutes=minutos_contratados),
        INICIO,
        INICIO + timedelta(hours=horas_reales, minutes=minutos_reales),
    )


def test_f01_devolucion_puntual() -> None:
    resultado = _facturar(48, 48)

    assert resultado.tipo_devolucion is TipoDevolucion.PUNTUAL
    assert resultado.bloques_facturados == 2
    assert resultado.importe_base == Decimal("20000.00")
    assert resultado.recargo_demora == Decimal("0.00")
    assert resultado.importe_final == Decimal("20000.00")


def test_f02_devolucion_anticipada_recalcula_con_tiempo_efectivo() -> None:
    resultado = _facturar(72, 30)

    assert resultado.tipo_devolucion is TipoDevolucion.ANTICIPADA
    assert resultado.horas_efectivas == Decimal("30")
    assert resultado.bloques_facturados == 2
    assert resultado.importe_base == Decimal("20000.00")
    assert resultado.importe_final == Decimal("20000.00")


def test_f03_anticipada_aplica_minimo_de_un_bloque() -> None:
    resultado = _facturar(24, 3)

    assert resultado.tipo_devolucion is TipoDevolucion.ANTICIPADA
    assert resultado.bloques_facturados == 1
    assert resultado.importe_base == Decimal("10000.00")
    assert resultado.importe_final == Decimal("10000.00")


def test_f04_anticipada_con_24_horas_exactas() -> None:
    resultado = _facturar(72, 24)

    assert resultado.tipo_devolucion is TipoDevolucion.ANTICIPADA
    assert resultado.bloques_facturados == 1
    assert resultado.importe_base == Decimal("10000.00")


def test_f05_limite_24_horas_y_un_minuto() -> None:
    resultado = _facturar(72, 24, minutos_reales=1)

    assert resultado.tipo_devolucion is TipoDevolucion.ANTICIPADA
    assert resultado.bloques_facturados == 2
    assert resultado.importe_base == Decimal("20000.00")


def test_f06_demora_de_dos_horas() -> None:
    resultado = _facturar(48, 50)

    assert resultado.tipo_devolucion is TipoDevolucion.TARDIA
    assert resultado.horas_demora == Decimal("2")
    assert resultado.importe_base == Decimal("20000.00")
    assert resultado.recargo_demora == Decimal("833.33")
    assert resultado.importe_final == Decimal("20833.33")


def test_f07_demora_fraccionaria_de_treinta_minutos() -> None:
    resultado = _facturar(48, 48, minutos_reales=30)

    assert resultado.tipo_devolucion is TipoDevolucion.TARDIA
    assert resultado.horas_demora == Decimal("0.5")
    assert resultado.importe_base == Decimal("20000.00")
    assert resultado.recargo_demora == Decimal("208.33")
    assert resultado.importe_final == Decimal("20208.33")


def test_f08_demora_de_un_minuto() -> None:
    resultado = _facturar(48, 48, minutos_reales=1)

    assert resultado.tipo_devolucion is TipoDevolucion.TARDIA
    assert resultado.horas_demora == Decimal(1) / Decimal(60)
    assert resultado.importe_base == Decimal("20000.00")
    assert resultado.recargo_demora == Decimal("6.94")
    assert resultado.importe_final == Decimal("20006.94")


def test_f09_usa_la_tarifa_acordada_y_no_la_vigente() -> None:
    tarifa_acordada = Decimal("10000.00")
    tarifa_vigente_actual = Decimal("12000.00")

    resultado = _facturar(24, 24, tarifa=tarifa_acordada)

    assert tarifa_vigente_actual != tarifa_acordada
    assert resultado.importe_final == Decimal("10000.00")


def test_f10_redondeo_half_up() -> None:
    resultado = _facturar(24, 25, tarifa=Decimal("1000.00"))

    assert resultado.importe_base == Decimal("1000.00")
    assert resultado.recargo_demora == Decimal("41.67")
    assert resultado.importe_final == Decimal("1041.67")


def test_f11_duracion_invalida_igual_a_cero() -> None:
    with pytest.raises(ErrorValidacion):
        calcular_facturacion(
            TARIFA,
            INICIO,
            INICIO + timedelta(hours=48),
            INICIO,
            INICIO,
        )


def test_f12_devolucion_anterior_al_retiro() -> None:
    with pytest.raises(ErrorValidacion):
        calcular_facturacion(
            TARIFA,
            INICIO,
            INICIO + timedelta(hours=48),
            INICIO,
            INICIO - timedelta(minutes=1),
        )


@pytest.mark.parametrize("tarifa", [Decimal("0.00"), Decimal("-0.01")])
def test_f13_tarifa_invalida(tarifa: Decimal) -> None:
    with pytest.raises(ErrorValidacion):
        _facturar(24, 24, tarifa=tarifa)


@pytest.mark.parametrize(
    ("horas_contratadas", "horas_reales", "minutos_reales"),
    [
        (72, 30, 0),
        (48, 48, 0),
        (48, 50, 0),
        (48, 48, 30),
        (48, 48, 1),
    ],
)
def test_f14_invariante_importe_final(
    horas_contratadas: int, horas_reales: int, minutos_reales: int
) -> None:
    resultado = _facturar(
        horas_contratadas, horas_reales, minutos_reales=minutos_reales
    )

    assert resultado.importe_final == (
        resultado.importe_base + resultado.recargo_demora
    )


def test_rechaza_float_para_importes() -> None:
    with pytest.raises(TypeError):
        _facturar(24, 24, tarifa=1000.0)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("horas", "bloques_esperados"),
    [
        (Decimal("0.01"), 1),
        (Decimal("3"), 1),
        (Decimal("24"), 1),
        (Decimal("24.000001"), 2),
        (Decimal("48"), 2),
        (Decimal("48.000001"), 3),
    ],
)
def test_calcular_bloques_24h(horas: Decimal, bloques_esperados: int) -> None:
    assert calcular_bloques_24h(horas) == bloques_esperados


def test_calcular_importe_estimado() -> None:
    assert calcular_importe_estimado(
        TARIFA, INICIO, INICIO + timedelta(hours=3)
    ) == Decimal("10000.00")
    assert calcular_importe_estimado(
        TARIFA, INICIO, INICIO + timedelta(hours=24, minutes=1)
    ) == Decimal("20000.00")
    assert calcular_importe_estimado(
        TARIFA, INICIO, INICIO + timedelta(hours=48)
    ) == Decimal("20000.00")
