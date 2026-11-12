"""Vista de inicio de alquileres y devoluciones."""

import tkinter as tk
from datetime import datetime
from tkinter import simpledialog

import customtkinter as ctk

from interfaz.componentes import (
    FORMATO_FECHA,
    cargar_tabla,
    crear_tabla,
    formatear_fecha,
    formatear_importe,
    id_seleccionado,
    mostrar_error,
    mostrar_info,
    parsear_fecha_hora,
)
from modelos.estados import EstadoAlquiler, EstadoReserva
from utilidades.excepciones import ErrorBaseDatos, ErrorValidacion


class VistaAlquileres(ctk.CTkFrame):
    """Tabla de alquileres con inicio y devolución."""

    def __init__(
        self,
        parent,
        servicio_alquileres,
        servicio_reservas,
        servicio_clientes,
        servicio_vehiculos,
        al_cambiar,
    ) -> None:
        super().__init__(parent, fg_color="transparent")
        self._servicio = servicio_alquileres
        self._reservas = servicio_reservas
        self._clientes = servicio_clientes
        self._vehiculos = servicio_vehiculos
        self._al_cambiar = al_cambiar

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.grid(row=0, column=0, sticky="ew")

        ctk.CTkLabel(
            barra,
            text="Alquileres",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(side="left")

        ctk.CTkButton(
            barra,
            text="Registrar devolución",
            width=150,
            command=self._devolver,
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            barra,
            text="Iniciar alquiler",
            width=120,
            command=self._iniciar,
        ).pack(side="right")

        contenedor, self._tabla = crear_tabla(
            self,
            [
                ("id", "ID", 50),
                ("cliente", "Cliente", 160),
                ("vehiculo", "Vehículo", 140),
                ("reserva", "Reserva", 70),
                ("retiro", "Retiro real", 125),
                ("devolucion", "Devolución real", 130),
                ("base", "Base", 90),
                ("recargo", "Recargo", 90),
                ("final", "Final", 95),
                ("estado", "Estado", 90),
            ],
        )
        contenedor.grid(row=1, column=0, sticky="nsew", pady=(10, 0))

        self.refrescar()

    def refrescar(self) -> None:
        try:
            alquileres = self._servicio.listar()
            reservas = {
                reserva.id: reserva
                for reserva in self._reservas.listar()
            }
            clientes = {
                cliente.id: cliente
                for cliente in self._clientes.listar(incluir_inactivos=True)
            }
            vehiculos = {
                vehiculo.id: vehiculo
                for vehiculo in self._vehiculos.listar(incluir_baja=True)
            }
        except ErrorBaseDatos as exc:
            mostrar_error(self, exc)
            return

        filas = []
        for alquiler in alquileres:
            reserva = reservas.get(alquiler.reserva_id)
            cliente = clientes.get(reserva.cliente_id) if reserva else None
            vehiculo = vehiculos.get(reserva.vehiculo_id) if reserva else None
            filas.append(
                (
                    alquiler.id,
                    self._texto_cliente(cliente)
                    if cliente
                    else "-",
                    self._texto_vehiculo(vehiculo)
                    if vehiculo
                    else "-",
                    alquiler.reserva_id,
                    formatear_fecha(alquiler.fecha_hora_retiro_real),
                    formatear_fecha(
                        alquiler.fecha_hora_devolucion_real
                    ),
                    formatear_importe(alquiler.importe_base),
                    formatear_importe(alquiler.recargo_demora),
                    formatear_importe(alquiler.importe_final),
                    alquiler.estado.value,
                )
            )

        cargar_tabla(self._tabla, filas)

    def _iniciar(self) -> None:
        try:
            alquileres = self._servicio.listar()
            con_alquiler = {alquiler.reserva_id for alquiler in alquileres}
            reservas = [
                reserva
                for reserva in self._reservas.listar()
                if reserva.estado is EstadoReserva.CONFIRMADA
                and reserva.id not in con_alquiler
            ]
            clientes = {
                cliente.id: cliente
                for cliente in self._clientes.listar(incluir_inactivos=True)
            }
            vehiculos = {
                vehiculo.id: vehiculo
                for vehiculo in self._vehiculos.listar(incluir_baja=True)
            }
        except ErrorBaseDatos as exc:
            mostrar_error(self, exc)
            return

        if not reservas:
            mostrar_info(
                self, "No hay reservas confirmadas pendientes de alquilar."
            )
            return

        reservas_por_texto = {
            self._texto_reserva(reserva, clientes, vehiculos): reserva
            for reserva in reservas
        }

        ventana = ctk.CTkToplevel(self)
        ventana.title("Iniciar alquiler")
        ventana.geometry("620x230")
        ventana.transient(self.winfo_toplevel())
        ventana.grab_set()
        ventana.grid_columnconfigure(1, weight=1)

        variable_reserva = tk.StringVar(
            value=next(iter(reservas_por_texto))
        )

        ctk.CTkLabel(ventana, text="Reserva").grid(
            row=0, column=0, sticky="w", padx=16, pady=10
        )
        selector = ctk.CTkOptionMenu(
            ventana,
            values=list(reservas_por_texto),
            variable=variable_reserva,
        )
        selector.grid(row=0, column=1, sticky="ew", padx=16, pady=10)

        ctk.CTkLabel(ventana, text="Retiro real").grid(
            row=1, column=0, sticky="w", padx=16, pady=10
        )
        entrada = ctk.CTkEntry(
            ventana, placeholder_text="AAAA-MM-DD HH:MM"
        )
        entrada.grid(row=1, column=1, sticky="ew", padx=16, pady=10)

        def actualizar_retiro(valor: str) -> None:
            reserva = reservas_por_texto[valor]
            entrada.delete(0, "end")
            entrada.insert(
                0,
                formatear_fecha(reserva.fecha_hora_retiro_prevista),
            )

        selector.configure(command=actualizar_retiro)
        actualizar_retiro(variable_reserva.get())

        acciones = ctk.CTkFrame(ventana, fg_color="transparent")
        acciones.grid(
            row=2, column=0, columnspan=2, pady=16, padx=16, sticky="e"
        )

        def guardar() -> None:
            try:
                reserva = reservas_por_texto[variable_reserva.get()]
                retiro_real = parsear_fecha_hora(
                    entrada.get(), "Retiro real"
                )
                self._servicio.iniciar(reserva.id, retiro_real)
            except (ErrorValidacion, ErrorBaseDatos) as exc:
                mostrar_error(ventana, exc)
                return

            ventana.destroy()
            self._al_cambiar()

        ctk.CTkButton(
            acciones, text="Cancelar", width=100, command=ventana.destroy
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            acciones, text="Iniciar", width=100, command=guardar
        ).pack(side="right")

    def _devolver(self) -> None:
        try:
            alquiler_id = id_seleccionado(self._tabla, "alquileres")
            alquiler = self._servicio.obtener(alquiler_id)
        except (ErrorValidacion, ErrorBaseDatos) as exc:
            mostrar_error(self, exc)
            return

        if alquiler.estado is not EstadoAlquiler.EN_CURSO:
            mostrar_error(
                self,
                ErrorValidacion(
                    "Solo se pueden cerrar alquileres en curso."
                ),
            )
            return

        texto = simpledialog.askstring(
            "Registrar devolución",
            "Fecha y hora de devolución (AAAA-MM-DD HH:MM):",
            initialvalue=datetime.now().strftime(FORMATO_FECHA),
            parent=self,
        )
        if texto is None:
            return

        try:
            devolucion = parsear_fecha_hora(texto, "Devolución real")
            cerrado = self._servicio.cerrar(alquiler_id, devolucion)
        except (ErrorValidacion, ErrorBaseDatos) as exc:
            mostrar_error(self, exc)
            return

        mostrar_info(
            self,
            "Alquiler cerrado.\n"
            f"Importe base: {formatear_importe(cerrado.importe_base)}\n"
            f"Recargo: {formatear_importe(cerrado.recargo_demora)}\n"
            f"Importe final: {formatear_importe(cerrado.importe_final)}",
        )
        self._al_cambiar()

    @staticmethod
    def _texto_cliente(cliente) -> str:
        return (
            f"{cliente.apellido}, {cliente.nombre} "
            f"({cliente.documento})"
        )

    @staticmethod
    def _texto_vehiculo(vehiculo) -> str:
        return f"{vehiculo.patente} - {vehiculo.marca} {vehiculo.modelo}"

    @classmethod
    def _texto_reserva(cls, reserva, clientes, vehiculos) -> str:
        cliente = clientes.get(reserva.cliente_id)
        vehiculo = vehiculos.get(reserva.vehiculo_id)
        return (
            f"{reserva.id} | "
            f"{cls._texto_cliente(cliente) if cliente else '-'} | "
            f"{cls._texto_vehiculo(vehiculo) if vehiculo else '-'} | "
            f"{formatear_fecha(reserva.fecha_hora_retiro_prevista)}"
        )
