"""Ventana principal de la aplicación."""

from tkinter import ttk

import customtkinter as ctk

from interfaz.vistas.vista_alquileres import VistaAlquileres
from interfaz.vistas.vista_clientes import VistaClientes
from interfaz.vistas.vista_reservas import VistaReservas
from interfaz.vistas.vista_vehiculos import VistaVehiculos
from servicios.servicio_alquileres import ServicioAlquileres
from servicios.servicio_clientes import ServicioClientes
from servicios.servicio_reservas import ServicioReservas
from servicios.servicio_vehiculos import ServicioVehiculos


class Aplicacion(ctk.CTk):
    """Ventana principal con pestañas para cada módulo."""

    def __init__(self, base_datos) -> None:
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        super().__init__()
        self.title("Car Rental System")
        self.geometry("1180x720")
        self.minsize(950, 600)

        self._base_datos = base_datos
        self._configurar_estilo()

        servicio_vehiculos = ServicioVehiculos(base_datos)
        servicio_clientes = ServicioClientes(base_datos)
        servicio_reservas = ServicioReservas(base_datos)
        servicio_alquileres = ServicioAlquileres(base_datos)

        self._tabview = ctk.CTkTabview(self)
        self._tabview.pack(fill="both", expand=True, padx=12, pady=12)

        nombres = ("Vehículos", "Clientes", "Reservas", "Alquileres")
        for nombre in nombres:
            self._tabview.add(nombre)

        self._vistas = {
            "Vehículos": VistaVehiculos(
                self._tabview.tab("Vehículos"),
                servicio_vehiculos,
                self.refrescar_todo,
            ),
            "Clientes": VistaClientes(
                self._tabview.tab("Clientes"),
                servicio_clientes,
                self.refrescar_todo,
            ),
            "Reservas": VistaReservas(
                self._tabview.tab("Reservas"),
                servicio_reservas,
                servicio_clientes,
                servicio_vehiculos,
                self.refrescar_todo,
            ),
            "Alquileres": VistaAlquileres(
                self._tabview.tab("Alquileres"),
                servicio_alquileres,
                servicio_reservas,
                servicio_clientes,
                servicio_vehiculos,
                self.refrescar_todo,
            ),
        }

        for vista in self._vistas.values():
            vista.pack(fill="both", expand=True)

        self._tabview.configure(command=self._al_cambiar_pestana)
        self.protocol("WM_DELETE_WINDOW", self._cerrar)
        self.refrescar_todo()

    def refrescar_todo(self) -> None:
        """Actualiza todas las vistas después de una operación."""
        for vista in self._vistas.values():
            vista.refrescar()

    def _al_cambiar_pestana(self, nombre: str | None = None) -> None:
        nombre = nombre or self._tabview.get()
        vista = self._vistas.get(nombre)
        if vista is not None:
            vista.refrescar()

    def _cerrar(self) -> None:
        self._base_datos.cerrar()
        self.destroy()

    def _configurar_estilo(self) -> None:
        estilo = ttk.Style(self)
        try:
            estilo.theme_use("clam")
        except Exception:
            pass
        estilo.configure("Treeview", rowheight=26)
        estilo.configure(
            "Treeview.Heading", font=("Segoe UI", 10, "bold")
        )
