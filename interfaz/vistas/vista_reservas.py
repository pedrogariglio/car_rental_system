"""Vista de reservas y disponibilidad."""

import tkinter as tk

import customtkinter as ctk

from interfaz.componentes import (
    cargar_tabla,
    confirmar,
    crear_tabla,
    formatear_fecha,
    formatear_importe,
    id_seleccionado,
    mostrar_error,
    mostrar_info,
    parsear_decimal,
    parsear_decimal_opcional,
    parsear_fecha_hora,
)
from modelos.estados import EstadoVehiculo
from utilidades.excepciones import ErrorBaseDatos, ErrorValidacion


class VistaReservas(ctk.CTkFrame):
    """Tabla de reservas y formulario de alta/modificación."""

    def __init__(
        self,
        parent,
        servicio_reservas,
        servicio_clientes,
        servicio_vehiculos,
        al_cambiar,
    ) -> None:
        super().__init__(parent, fg_color="transparent")
        self._servicio = servicio_reservas
        self._clientes = servicio_clientes
        self._vehiculos = servicio_vehiculos
        self._al_cambiar = al_cambiar

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.grid(row=0, column=0, sticky="ew")

        ctk.CTkLabel(
            barra,
            text="Reservas",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(side="left")

        for texto, comando in (
            ("Nueva", self._nueva),
            ("Modificar", self._modificar),
            ("Cancelar", self._cancelar),
        ):
            ctk.CTkButton(
                barra, text=texto, width=100, command=comando
            ).pack(side="right", padx=(8, 0))

        contenedor, self._tabla = crear_tabla(
            self,
            [
                ("id", "ID", 50),
                ("cliente", "Cliente", 170),
                ("vehiculo", "Vehículo", 150),
                ("retiro", "Retiro previsto", 125),
                ("devolucion", "Devolución prevista", 135),
                ("tarifa", "Tarifa", 90),
                ("estimado", "Estimado", 100),
                ("estado", "Estado", 100),
            ],
        )
        contenedor.grid(row=1, column=0, sticky="nsew", pady=(10, 0))

        self.refrescar()

    def refrescar(self) -> None:
        try:
            reservas = self._servicio.listar()
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
        for reserva in reservas:
            cliente = clientes.get(reserva.cliente_id)
            vehiculo = vehiculos.get(reserva.vehiculo_id)
            filas.append(
                (
                    reserva.id,
                    self._texto_cliente(cliente)
                    if cliente
                    else f"Cliente {reserva.cliente_id}",
                    self._texto_vehiculo(vehiculo)
                    if vehiculo
                    else f"Vehículo {reserva.vehiculo_id}",
                    formatear_fecha(reserva.fecha_hora_retiro_prevista),
                    formatear_fecha(reserva.fecha_hora_devolucion_prevista),
                    formatear_importe(reserva.tarifa_diaria_acordada),
                    formatear_importe(reserva.importe_estimado),
                    reserva.estado.value,
                )
            )

        cargar_tabla(self._tabla, filas)

    def _nueva(self) -> None:
        self._abrir_formulario()

    def _modificar(self) -> None:
        try:
            reserva_id = id_seleccionado(self._tabla, "reservas")
            reserva = self._servicio.obtener(reserva_id)
        except (ErrorValidacion, ErrorBaseDatos) as exc:
            mostrar_error(self, exc)
            return
        self._abrir_formulario(reserva)

    def _cancelar(self) -> None:
        try:
            reserva_id = id_seleccionado(self._tabla, "reservas")
        except ErrorValidacion as exc:
            mostrar_error(self, exc)
            return

        if not confirmar(self, "¿Cancelar la reserva seleccionada?"):
            return

        try:
            self._servicio.cancelar(reserva_id)
        except (ErrorValidacion, ErrorBaseDatos) as exc:
            mostrar_error(self, exc)
            return

        self._al_cambiar()

    def _abrir_formulario(self, reserva=None) -> None:
        try:
            clientes = self._clientes.listar()
            vehiculos = [
                vehiculo
                for vehiculo in self._vehiculos.listar()
                if vehiculo.estado is not EstadoVehiculo.MANTENIMIENTO
            ]

            if reserva is not None:
                cliente_actual = self._clientes.obtener(reserva.cliente_id)
                vehiculo_actual = self._vehiculos.obtener(
                    reserva.vehiculo_id
                )
                if all(c.id != cliente_actual.id for c in clientes):
                    clientes.append(cliente_actual)
                if all(v.id != vehiculo_actual.id for v in vehiculos):
                    vehiculos.append(vehiculo_actual)
        except (ErrorValidacion, ErrorBaseDatos) as exc:
            mostrar_error(self, exc)
            return

        if not clientes or not vehiculos:
            mostrar_error(
                self,
                ErrorValidacion(
                    "Debe haber al menos un cliente activo y un vehículo "
                    "disponible para reservar."
                ),
            )
            return

        clientes_por_texto = {
            self._texto_cliente(cliente): cliente for cliente in clientes
        }
        vehiculos_por_texto = {
            self._texto_vehiculo(vehiculo): vehiculo
            for vehiculo in vehiculos
        }

        ventana = ctk.CTkToplevel(self)
        ventana.title("Reserva")
        ventana.geometry("560x400")
        ventana.transient(self.winfo_toplevel())
        ventana.grab_set()
        ventana.grid_columnconfigure(1, weight=1)

        texto_cliente_inicial = (
            self._texto_cliente(
                next(
                    cliente
                    for cliente in clientes
                    if reserva and cliente.id == reserva.cliente_id
                )
            )
            if reserva
            else next(iter(clientes_por_texto))
        )
        texto_vehiculo_inicial = (
            self._texto_vehiculo(
                next(
                    vehiculo
                    for vehiculo in vehiculos
                    if reserva and vehiculo.id == reserva.vehiculo_id
                )
            )
            if reserva
            else next(iter(vehiculos_por_texto))
        )

        variable_cliente = tk.StringVar(value=texto_cliente_inicial)
        variable_vehiculo = tk.StringVar(value=texto_vehiculo_inicial)

        ctk.CTkLabel(ventana, text="Cliente").grid(
            row=0, column=0, sticky="w", padx=16, pady=8
        )
        selector_cliente = ctk.CTkOptionMenu(
            ventana,
            values=list(clientes_por_texto),
            variable=variable_cliente,
        )
        selector_cliente.grid(
            row=0, column=1, sticky="ew", padx=16, pady=8
        )

        ctk.CTkLabel(ventana, text="Vehículo").grid(
            row=1, column=0, sticky="w", padx=16, pady=8
        )
        selector_vehiculo = ctk.CTkOptionMenu(
            ventana,
            values=list(vehiculos_por_texto),
            variable=variable_vehiculo,
        )
        selector_vehiculo.grid(
            row=1, column=1, sticky="ew", padx=16, pady=8
        )

        ctk.CTkLabel(ventana, text="Retiro previsto").grid(
            row=2, column=0, sticky="w", padx=16, pady=8
        )
        entrada_retiro = ctk.CTkEntry(
            ventana, placeholder_text="AAAA-MM-DD HH:MM"
        )
        entrada_retiro.grid(
            row=2, column=1, sticky="ew", padx=16, pady=8
        )

        ctk.CTkLabel(ventana, text="Devolución prevista").grid(
            row=3, column=0, sticky="w", padx=16, pady=8
        )
        entrada_devolucion = ctk.CTkEntry(
            ventana, placeholder_text="AAAA-MM-DD HH:MM"
        )
        entrada_devolucion.grid(
            row=3, column=1, sticky="ew", padx=16, pady=8
        )

        ctk.CTkLabel(
            ventana, text="Tarifa (vacío = tarifa del vehículo)"
        ).grid(row=4, column=0, sticky="w", padx=16, pady=8)
        entrada_tarifa = ctk.CTkEntry(ventana)
        entrada_tarifa.grid(
            row=4, column=1, sticky="ew", padx=16, pady=8
        )

        if reserva is not None:
            entrada_retiro.insert(
                0, formatear_fecha(reserva.fecha_hora_retiro_prevista)
            )
            entrada_devolucion.insert(
                0, formatear_fecha(reserva.fecha_hora_devolucion_prevista)
            )
            entrada_tarifa.insert(0, str(reserva.tarifa_diaria_acordada))
            selector_cliente.configure(state="disabled")
            selector_vehiculo.configure(state="disabled")

        acciones = ctk.CTkFrame(ventana, fg_color="transparent")
        acciones.grid(
            row=5, column=0, columnspan=2, pady=16, padx=16, sticky="ew"
        )

        def verificar_disponibilidad() -> None:
            try:
                cliente = clientes_por_texto[variable_cliente.get()]
                vehiculo = vehiculos_por_texto[variable_vehiculo.get()]
                retiro = parsear_fecha_hora(
                    entrada_retiro.get(), "Retiro previsto"
                )
                devolucion = parsear_fecha_hora(
                    entrada_devolucion.get(), "Devolución prevista"
                )
                disponible = self._servicio.consultar_disponibilidad(
                    vehiculo.id,
                    retiro,
                    devolucion,
                    excluir_reserva_id=reserva.id if reserva else None,
                )
            except (ErrorValidacion, ErrorBaseDatos) as exc:
                mostrar_error(ventana, exc)
                return

            mensaje = (
                f"El vehículo está disponible para "
                f"{self._texto_cliente(cliente)}."
                if disponible
                else "El vehículo no está disponible para ese período."
            )
            mostrar_info(ventana, mensaje)

        def guardar() -> None:
            try:
                retiro = parsear_fecha_hora(
                    entrada_retiro.get(), "Retiro previsto"
                )
                devolucion = parsear_fecha_hora(
                    entrada_devolucion.get(), "Devolución prevista"
                )

                if reserva is None:
                    cliente = clientes_por_texto[variable_cliente.get()]
                    vehiculo = vehiculos_por_texto[
                        variable_vehiculo.get()
                    ]
                    tarifa = parsear_decimal_opcional(
                        entrada_tarifa.get(), "Tarifa"
                    )
                    self._servicio.crear(
                        cliente.id,
                        vehiculo.id,
                        retiro,
                        devolucion,
                        tarifa,
                    )
                else:
                    cambios = {
                        "fecha_hora_retiro_prevista": retiro,
                        "fecha_hora_devolucion_prevista": devolucion,
                    }
                    if entrada_tarifa.get().strip():
                        cambios["tarifa_diaria_acordada"] = (
                            parsear_decimal(
                                entrada_tarifa.get(), "Tarifa"
                            )
                        )
                    self._servicio.modificar(reserva.id, **cambios)
            except (ErrorValidacion, ErrorBaseDatos) as exc:
                mostrar_error(ventana, exc)
                return

            ventana.destroy()
            self._al_cambiar()

        ctk.CTkButton(
            acciones,
            text="Verificar disponibilidad",
            width=160,
            command=verificar_disponibilidad,
        ).pack(side="left")
        ctk.CTkButton(
            acciones, text="Cancelar", width=100, command=ventana.destroy
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            acciones, text="Guardar", width=100, command=guardar
        ).pack(side="right")

    @staticmethod
    def _texto_cliente(cliente) -> str:
        return (
            f"{cliente.apellido}, {cliente.nombre} "
            f"({cliente.documento})"
        )

    @staticmethod
    def _texto_vehiculo(vehiculo) -> str:
        return f"{vehiculo.patente} - {vehiculo.marca} {vehiculo.modelo}"
