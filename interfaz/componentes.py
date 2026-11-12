"""Componentes y funciones compartidas por las vistas."""

from datetime import datetime
from decimal import Decimal, InvalidOperation
from tkinter import messagebox, ttk

import customtkinter as ctk

from utilidades.excepciones import ErrorValidacion

FORMATO_FECHA = "%Y-%m-%d %H:%M"


def formatear_fecha(valor: datetime | None) -> str:
    """Formatea una fecha para mostrar en tablas o formularios."""
    return valor.strftime(FORMATO_FECHA) if valor is not None else "-"


def formatear_importe(valor: Decimal | None) -> str:
    """Formatea un importe monetario."""
    return "-" if valor is None else f"${valor:,.2f}"


def parsear_fecha_hora(texto: str, campo: str) -> datetime:
    """Convierte un texto AAAA-MM-DD HH:MM a datetime."""
    try:
        return datetime.strptime(texto.strip(), FORMATO_FECHA)
    except (AttributeError, ValueError) as exc:
        raise ErrorValidacion(
            f"{campo}: use el formato AAAA-MM-DD HH:MM."
        ) from exc


def parsear_decimal(texto: str, campo: str) -> Decimal:
    """Convierte un texto a Decimal obligatorio."""
    valor = parsear_decimal_opcional(texto, campo)
    if valor is None:
        raise ErrorValidacion(f"{campo} es obligatorio.")
    return valor


def parsear_decimal_opcional(texto: str, campo: str) -> Decimal | None:
    """Convierte un texto a Decimal, permitiendo vacío."""
    limpio = texto.strip()
    if not limpio:
        return None

    try:
        return Decimal(limpio)
    except InvalidOperation as exc:
        raise ErrorValidacion(f"{campo} debe ser un número válido.") from exc


def parsear_entero(texto: str, campo: str) -> int:
    """Convierte un texto a entero."""
    try:
        return int(texto.strip())
    except (AttributeError, ValueError) as exc:
        raise ErrorValidacion(f"{campo} debe ser un número entero.") from exc


def crear_tabla(
    parent,
    columnas: list[tuple[str, str, int]],
    altura: int = 12,
) -> tuple[ctk.CTkFrame, ttk.Treeview]:
    """Crea una tabla con encabezados y barra vertical."""
    contenedor = ctk.CTkFrame(parent, fg_color="transparent")
    tabla = ttk.Treeview(
        contenedor,
        columns=[columna[0] for columna in columnas],
        show="headings",
        height=altura,
    )

    for clave, titulo, ancho in columnas:
        tabla.heading(clave, text=titulo)
        tabla.column(clave, width=ancho, anchor="center", stretch=True)

    barra = ttk.Scrollbar(contenedor, orient="vertical", command=tabla.yview)
    tabla.configure(yscrollcommand=barra.set)
    tabla.pack(side="left", fill="both", expand=True)
    barra.pack(side="right", fill="y")

    return contenedor, tabla


def cargar_tabla(tabla: ttk.Treeview, filas: list[tuple]) -> None:
    """Reemplaza el contenido de una tabla.

    El primer elemento de cada fila se usa como identificador oculto.
    """
    for item in tabla.get_children():
        tabla.delete(item)

    for fila in filas:
        tabla.insert("", "end", iid=str(fila[0]), values=fila[1:])


def id_seleccionado(tabla: ttk.Treeview, entidad: str) -> int:
    """Devuelve el id de la fila seleccionada."""
    seleccion = tabla.selection()
    if not seleccion:
        raise ErrorValidacion(f"Seleccione un registro de {entidad}.")
    return int(seleccion[0])


def mostrar_error(parent, error: Exception) -> None:
    """Muestra un error en un diálogo."""
    messagebox.showerror("Error", str(error), parent=parent)


def mostrar_info(parent, mensaje: str) -> None:
    """Muestra un mensaje informativo."""
    messagebox.showinfo("Información", mensaje, parent=parent)


def confirmar(parent, mensaje: str) -> bool:
    """Solicita confirmación al usuario."""
    return messagebox.askyesno("Confirmar", mensaje, parent=parent)
