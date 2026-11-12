"""Vista de administración de vehículos."""

import customtkinter as ctk

from interfaz.componentes import (
    cargar_tabla,
    confirmar,
    crear_tabla,
    formatear_importe,
    id_seleccionado,
    mostrar_error,
    parsear_decimal,
    parsear_entero,
)
from modelos.estados import EstadoVehiculo
from utilidades.excepciones import ErrorBaseDatos, ErrorValidacion


class VistaVehiculos(ctk.CTkFrame):
    """Tabla y formulario básico de vehículos."""

    def __init__(self, parent, servicio, al_cambiar) -> None:
        super().__init__(parent, fg_color="transparent")
        self._servicio = servicio
        self._al_cambiar = al_cambiar

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.grid(row=0, column=0, sticky="ew")

        ctk.CTkLabel(
            barra,
            text="Vehículos",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(side="left")

        for texto, comando in (
            ("Nuevo", self._nuevo),
            ("Editar", self._editar),
            ("Dar de baja", self._dar_de_baja),
            ("Reactivar", self._reactivar),
        ):
            ctk.CTkButton(
                barra, text=texto, width=100, command=comando
            ).pack(side="right", padx=(8, 0))

        contenedor, self._tabla = crear_tabla(
            self,
            [
                ("id", "ID", 50),
                ("patente", "Patente", 100),
                ("marca", "Marca", 100),
                ("modelo", "Modelo", 110),
                ("anio", "Año", 60),
                ("categoria", "Categoría", 100),
                ("tarifa", "Tarifa diaria", 110),
                ("estado", "Estado", 110),
            ],
        )
        contenedor.grid(row=1, column=0, sticky="nsew", pady=(10, 0))

        self.refrescar()

    def refrescar(self) -> None:
        try:
            vehiculos = self._servicio.listar(incluir_baja=True)
        except ErrorBaseDatos as exc:
            mostrar_error(self, exc)
            return

        cargar_tabla(
            self._tabla,
            [
                (
                    vehiculo.id,
                    vehiculo.patente,
                    vehiculo.marca,
                    vehiculo.modelo,
                    vehiculo.anio,
                    vehiculo.categoria,
                    formatear_importe(vehiculo.tarifa_diaria),
                    vehiculo.estado.value,
                )
                for vehiculo in vehiculos
            ],
        )

    def _nuevo(self) -> None:
        self._abrir_formulario()

    def _editar(self) -> None:
        try:
            vehiculo_id = id_seleccionado(self._tabla, "vehículos")
            vehiculo = self._servicio.obtener(vehiculo_id)
        except (ErrorValidacion, ErrorBaseDatos) as exc:
            mostrar_error(self, exc)
            return
        self._abrir_formulario(vehiculo)

    def _dar_de_baja(self) -> None:
        try:
            vehiculo_id = id_seleccionado(self._tabla, "vehículos")
        except ErrorValidacion as exc:
            mostrar_error(self, exc)
            return

        if not confirmar(self, "¿Dar de baja el vehículo seleccionado?"):
            return

        try:
            self._servicio.dar_de_baja(vehiculo_id)
        except (ErrorValidacion, ErrorBaseDatos) as exc:
            mostrar_error(self, exc)
            return

        self._al_cambiar()

    def _reactivar(self) -> None:
        try:
            vehiculo_id = id_seleccionado(self._tabla, "vehículos")
            self._servicio.cambiar_estado(
                vehiculo_id, EstadoVehiculo.DISPONIBLE
            )
        except (ErrorValidacion, ErrorBaseDatos) as exc:
            mostrar_error(self, exc)
            return

        self._al_cambiar()

    def _abrir_formulario(self, vehiculo=None) -> None:
        ventana = ctk.CTkToplevel(self)
        ventana.title("Vehículo")
        ventana.geometry("440x420")
        ventana.transient(self.winfo_toplevel())
        ventana.grab_set()
        ventana.grid_columnconfigure(1, weight=1)

        campos = [
            ("patente", "Patente", vehiculo.patente if vehiculo else ""),
            ("marca", "Marca", vehiculo.marca if vehiculo else ""),
            ("modelo", "Modelo", vehiculo.modelo if vehiculo else ""),
            ("anio", "Año", vehiculo.anio if vehiculo else ""),
            (
                "categoria",
                "Categoría",
                vehiculo.categoria if vehiculo else "",
            ),
            (
                "tarifa",
                "Tarifa diaria",
                vehiculo.tarifa_diaria if vehiculo else "",
            ),
        ]

        entradas = {}
        for fila, (clave, etiqueta, valor) in enumerate(campos):
            ctk.CTkLabel(ventana, text=etiqueta).grid(
                row=fila, column=0, sticky="w", padx=16, pady=6
            )
            entrada = ctk.CTkEntry(ventana)
            if valor != "":
                entrada.insert(0, str(valor))
            entrada.grid(
                row=fila, column=1, sticky="ew", padx=16, pady=6
            )
            entradas[clave] = entrada

        acciones = ctk.CTkFrame(ventana, fg_color="transparent")
        acciones.grid(
            row=len(campos), column=0, columnspan=2, pady=16, padx=16, sticky="e"
        )

        def guardar() -> None:
            try:
                datos = {
                    "patente": entradas["patente"].get(),
                    "marca": entradas["marca"].get(),
                    "modelo": entradas["modelo"].get(),
                    "anio": parsear_entero(
                        entradas["anio"].get(), "Año"
                    ),
                    "categoria": entradas["categoria"].get(),
                    "tarifa_diaria": parsear_decimal(
                        entradas["tarifa"].get(), "Tarifa diaria"
                    ),
                }

                if vehiculo is None:
                    self._servicio.registrar(**datos)
                else:
                    self._servicio.modificar(vehiculo.id, **datos)
            except (ErrorValidacion, ErrorBaseDatos) as exc:
                mostrar_error(ventana, exc)
                return

            ventana.destroy()
            self._al_cambiar()

        ctk.CTkButton(
            acciones, text="Cancelar", width=100, command=ventana.destroy
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            acciones, text="Guardar", width=100, command=guardar
        ).pack(side="right")
