"""Cálculo de importes de reservas y alquileres.

Este módulo es puro: no accede a MySQL ni a la interfaz gráfica.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal

from modelos.estados import TipoDevolucion
from utilidades.validaciones import (
    a_decimal,
    validar_fecha_hora,
    validar_misma_zona_horaria,
    validar_rango_fechas,
)

HORAS_POR_DIA = Decimal("24")
SEGUNDOS_POR_HORA = Decimal("3600")
MICROSEGUNDOS_POR_SEGUNDO = Decimal("1000000")
CENTIMOS = Decimal("0.01")
CERO = Decimal("0.00")


@dataclass(frozen=True)
class ResultadoFacturacion:
    """Desglose económico calculado para una devolución."""

    tipo_devolucion: TipoDevolucion
    horas_contratadas: Decimal
    horas_efectivas: Decimal
    horas_demora: Decimal
    bloques_facturados: int
    importe_base: Decimal
    recargo_demora: Decimal
    importe_final: Decimal


def calcular_bloques_24h(horas: Decimal) -> int:
    """Calcula bloques de 24 horas con redondeo hacia arriba y mínimo uno."""
    horas_decimal = a_decimal(horas, "horas", positivo=True)
    bloques = (horas_decimal / HORAS_POR_DIA).to_integral_value(
        rounding=ROUND_CEILING
    )
    return max(1, int(bloques))


def calcular_importe_estimado(
    tarifa_diaria_acordada: Decimal,
    fecha_hora_retiro_prevista: datetime,
    fecha_hora_devolucion_prevista: datetime,
) -> Decimal:
    """Calcula el importe estimado de una reserva según el período contratado."""
    tarifa = a_decimal(
        tarifa_diaria_acordada, "tarifa_diaria_acordada", positivo=True
    )
    horas_contratadas = _horas_entre(
        fecha_hora_retiro_prevista,
        fecha_hora_devolucion_prevista,
        nombre_inicio="fecha_hora_retiro_prevista",
        nombre_fin="fecha_hora_devolucion_prevista",
    )
    bloques = calcular_bloques_24h(horas_contratadas)
    return _calcular_importe_base(tarifa, bloques)


def calcular_facturacion(
    tarifa_diaria_acordada: Decimal,
    fecha_hora_retiro_prevista: datetime,
    fecha_hora_devolucion_prevista: datetime,
    fecha_hora_retiro_real: datetime,
    fecha_hora_devolucion_real: datetime,
) -> ResultadoFacturacion:
    """Calcula el desglose económico de un alquiler al registrar la devolución."""
    tarifa = a_decimal(
        tarifa_diaria_acordada, "tarifa_diaria_acordada", positivo=True
    )

    retiro_previsto = validar_fecha_hora(
        fecha_hora_retiro_prevista, "fecha_hora_retiro_prevista"
    )
    devolucion_prevista = validar_fecha_hora(
        fecha_hora_devolucion_prevista, "fecha_hora_devolucion_prevista"
    )
    retiro_real = validar_fecha_hora(
        fecha_hora_retiro_real, "fecha_hora_retiro_real"
    )
    devolucion_real = validar_fecha_hora(
        fecha_hora_devolucion_real, "fecha_hora_devolucion_real"
    )

    validar_misma_zona_horaria(
        (retiro_previsto, devolucion_prevista, retiro_real, devolucion_real)
    )

    horas_contratadas = _horas_entre(
        retiro_previsto,
        devolucion_prevista,
        nombre_inicio="fecha_hora_retiro_prevista",
        nombre_fin="fecha_hora_devolucion_prevista",
    )
    horas_efectivas = _horas_entre(
        retiro_real,
        devolucion_real,
        nombre_inicio="fecha_hora_retiro_real",
        nombre_fin="fecha_hora_devolucion_real",
    )

    if devolucion_real < devolucion_prevista:
        tipo_devolucion = TipoDevolucion.ANTICIPADA
        horas_facturadas = horas_efectivas
        horas_demora = CERO
    elif devolucion_real == devolucion_prevista:
        tipo_devolucion = TipoDevolucion.PUNTUAL
        horas_facturadas = horas_contratadas
        horas_demora = CERO
    else:
        tipo_devolucion = TipoDevolucion.TARDIA
        horas_facturadas = horas_contratadas
        horas_demora = _horas_entre(
            devolucion_prevista,
            devolucion_real,
            nombre_inicio="fecha_hora_devolucion_prevista",
            nombre_fin="fecha_hora_devolucion_real",
        )

    bloques = calcular_bloques_24h(horas_facturadas)
    importe_base = _calcular_importe_base(tarifa, bloques)
    recargo_exacto = (
        horas_demora * tarifa / HORAS_POR_DIA
        if tipo_devolucion is TipoDevolucion.TARDIA
        else CERO
    )
    importe_final = (importe_base + recargo_exacto).quantize(
        CENTIMOS, rounding=ROUND_HALF_UP
    )
    recargo_demora = importe_final - importe_base

    return ResultadoFacturacion(
        tipo_devolucion=tipo_devolucion,
        horas_contratadas=horas_contratadas,
        horas_efectivas=horas_efectivas,
        horas_demora=horas_demora,
        bloques_facturados=bloques,
        importe_base=importe_base,
        recargo_demora=recargo_demora,
        importe_final=importe_final,
    )


def _horas_entre(
    inicio: datetime,
    fin: datetime,
    *,
    nombre_inicio: str,
    nombre_fin: str,
) -> Decimal:
    """Calcula horas exactas entre dos fechas usando Decimal, sin float."""
    inicio_validado, fin_validado = validar_rango_fechas(
        inicio,
        fin,
        nombre_inicio=nombre_inicio,
        nombre_fin=nombre_fin,
    )
    diferencia = fin_validado - inicio_validado
    segundos = Decimal(diferencia.days * 86400 + diferencia.seconds)
    segundos += Decimal(diferencia.microseconds) / MICROSEGUNDOS_POR_SEGUNDO
    return segundos / SEGUNDOS_POR_HORA


def _calcular_importe_base(tarifa: Decimal, bloques: int) -> Decimal:
    return (tarifa * bloques).quantize(CENTIMOS, rounding=ROUND_HALF_UP)
