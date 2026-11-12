"""Punto de entrada de Car Rental System."""

from tkinter import Tk, messagebox

from config import obtener_config_bd
from db import BaseDatos
from interfaz.app import Aplicacion
from utilidades.excepciones import ErrorBaseDatos, ErrorConfiguracion


def main() -> int:
    """Inicia la conexión y abre la ventana principal."""
    try:
        base_datos = BaseDatos(obtener_config_bd())
        base_datos.conectar()
    except (ErrorConfiguracion, ErrorBaseDatos) as exc:
        raiz = Tk()
        raiz.withdraw()
        messagebox.showerror("No se pudo iniciar", str(exc))
        raiz.destroy()
        return 1

    try:
        aplicacion = Aplicacion(base_datos)
        aplicacion.mainloop()
    finally:
        base_datos.cerrar()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
