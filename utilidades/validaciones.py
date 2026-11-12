"""Validaciones y conversiones reutilizables."""

from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import TypeVar

from utilidades.excepciones import ErrorValidacion

TipoEnum = TypeVar("TipoEnum", bound=Enum)


def a_decimal(
    valor: object,
    campo: str,
    *,
    positivo: bool = False,
    no_negativo: bool = False,
) -> Decimal:
    """Convierte un valor a Decimal y valida su signo.

    Se rechazan los ``float`` para evitar errores de representación monetaria.
    """
    if isinstance(valor, bool) or isinstance(valor, float):
        raise TypeError(f"{campo} debe ser Decimal, int o str; no se admite float.")

    try:
        numero = valor if isinstance(valor, Decimal) else Decimal(str(valor))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ErrorValidacion(f"{campo} debe ser un número decimal válido.") from exc

    if not numero.is_finite():
        raise ErrorValidacion(f"{campo} debe ser un número finito.")

    if no_negativo and numero < 0:
        raise ErrorValidacion(f"{campo} no puede ser negativo.")

    if positivo and numero <= 0:
        raise ErrorValidacion(f"{campo} debe ser mayor que cero.")

    return numero


def validar_texto(valor: object, campo: str) -> str:
    """Valida que un texto obligatorio no esté vacío."""
    if not isinstance(valor, str):
        raise TypeError(f"{campo} debe ser texto.")

    texto = valor.strip()
    if not texto:
        raise ErrorValidacion(f"{campo} es obligatorio.")

    return texto


def validar_texto_opcional(valor: object, campo: str) -> str | None:
    """Valida un texto opcional y normaliza los vacíos a None."""
    if valor is None:
        return None
    if not isinstance(valor, str):
        raise TypeError(f"{campo} debe ser texto o None.")

    texto = valor.strip()
    return texto or None


def validar_entero_positivo(valor: object, campo: str) -> int:
    """Valida un entero mayor que cero."""
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise TypeError(f"{campo} debe ser un entero.")

    if valor <= 0:
        raise ErrorValidacion(f"{campo} debe ser mayor que cero.")

    return valor


def validar_fecha_hora(valor: object, campo: str) -> datetime:
    """Valida que el valor sea un datetime."""
    if not isinstance(valor, datetime):
        raise TypeError(f"{campo} debe ser un datetime.")

    return valor


def validar_rango_fechas(
    inicio: object,
    fin: object,
    *,
    nombre_inicio: str = "inicio",
    nombre_fin: str = "fin",
) -> tuple[datetime, datetime]:
    """Valida que ambas fechas sean datetime y que fin sea posterior a inicio."""
    fecha_inicio = validar_fecha_hora(inicio, nombre_inicio)
    fecha_fin = validar_fecha_hora(fin, nombre_fin)

    try:
        if fecha_fin <= fecha_inicio:
            raise ErrorValidacion(
                f"{nombre_fin} debe ser posterior a {nombre_inicio}."
            )
    except TypeError as exc:
        raise ErrorValidacion(
            f"{nombre_inicio} y {nombre_fin} deben tener la misma zona horaria."
        ) from exc

    return fecha_inicio, fecha_fin


def validar_misma_zona_horaria(fechas: tuple[datetime, ...]) -> None:
    """Valida que todas las fechas sean naive o todas conscientes de zona."""
    if len({fecha.tzinfo is None for fecha in fechas}) > 1:
        raise ErrorValidacion("Las fechas deben tener la misma zona horaria.")


def validar_enum(valor: object, tipo_enum: type[TipoEnum], campo: str) -> TipoEnum:
    """Convierte y valida un valor contra un Enum del dominio."""
    if isinstance(valor, tipo_enum):
        return valor

    try:
        return tipo_enum(valor)
    except (ValueError, TypeError) as exc:
        raise ErrorValidacion(f"{campo} no es un estado válido: {valor!r}.") from exc


def validar_campos_permitidos(
    cambios: dict, permitidos: set[str] | frozenset[str]
) -> None:
    """Rechaza claves que no correspondan a campos modificables."""
    invalidos = set(cambios) - set(permitidos)
    if invalidos:
        campos = ", ".join(sorted(invalidos))
        raise ErrorValidacion(f"Campos no permitidos para modificar: {campos}.")
