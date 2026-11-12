"""Vista de administración de clientes."""

import customtkinter as ctk

from interfaz.componentes import (
    cargar_tabla,
    confirmar,
    crear_tabla,
    id_seleccionado,
    mostrar_error,
)
from utilidades.excepciones import ErrorBaseDatos, ErrorValidacion


class VistaClientes(ctk.CTkFrame):
    """Tabla y formulario básico de clientes."""

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
            text="Clientes",
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
                ("documento", "Documento", 110),
                ("nombre", "Nombre", 120),
                ("apellido", "Apellido", 120),
                ("telefono", "Teléfono", 110),
                ("correo", "Correo", 180),
                ("activo", "Activo", 70),
            ],
        )
        contenedor.grid(row=1, column=0, sticky="nsew", pady=(10, 0))

        self.refrescar()

    def refrescar(self) -> None:
        try:
            clientes = self._servicio.listar(incluir_inactivos=True)
        except ErrorBaseDatos as exc:
            mostrar_error(self, exc)
            return

        cargar_tabla(
            self._tabla,
            [
                (
                    cliente.id,
                    cliente.documento,
                    cliente.nombre,
                    cliente.apellido,
                    cliente.telefono or "-",
                    cliente.correo_electronico or "-",
                    "Sí" if cliente.activo else "No",
                )
                for cliente in clientes
            ],
        )

    def _nuevo(self) -> None:
        self._abrir_formulario()

    def _editar(self) -> None:
        try:
            cliente_id = id_seleccionado(self._tabla, "clientes")
            cliente = self._servicio.obtener(cliente_id)
        except (ErrorValidacion, ErrorBaseDatos) as exc:
            mostrar_error(self, exc)
            return
        self._abrir_formulario(cliente)

    def _dar_de_baja(self) -> None:
        try:
            cliente_id = id_seleccionado(self._tabla, "clientes")
        except ErrorValidacion as exc:
            mostrar_error(self, exc)
            return

        if not confirmar(self, "¿Dar de baja el cliente seleccionado?"):
            return

        try:
            self._servicio.dar_de_baja(cliente_id)
        except (ErrorValidacion, ErrorBaseDatos) as exc:
            mostrar_error(self, exc)
            return

        self._al_cambiar()

    def _reactivar(self) -> None:
        try:
            cliente_id = id_seleccionado(self._tabla, "clientes")
            self._servicio.reactivar(cliente_id)
        except (ErrorValidacion, ErrorBaseDatos) as exc:
            mostrar_error(self, exc)
            return

        self._al_cambiar()

    def _abrir_formulario(self, cliente=None) -> None:
        ventana = ctk.CTkToplevel(self)
        ventana.title("Cliente")
        ventana.geometry("440x390")
        ventana.transient(self.winfo_toplevel())
        ventana.grab_set()
        ventana.grid_columnconfigure(1, weight=1)

        campos = [
            (
                "documento",
                "Documento",
                cliente.documento if cliente else "",
            ),
            ("nombre", "Nombre", cliente.nombre if cliente else ""),
            ("apellido", "Apellido", cliente.apellido if cliente else ""),
            (
                "telefono",
                "Teléfono",
                (cliente.telefono or "") if cliente else "",
            ),
            (
                "correo_electronico",
                "Correo",
                (cliente.correo_electronico or "") if cliente else "",
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
                    "documento": entradas["documento"].get(),
                    "nombre": entradas["nombre"].get(),
                    "apellido": entradas["apellido"].get(),
                    "telefono": entradas["telefono"].get(),
                    "correo_electronico": entradas[
                        "correo_electronico"
                    ].get(),
                }

                if cliente is None:
                    self._servicio.registrar(**datos)
                else:
                    self._servicio.modificar(cliente.id, **datos)
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
