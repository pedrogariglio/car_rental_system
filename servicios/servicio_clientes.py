"""Reglas de negocio para la administración de clientes."""

from dataclasses import replace

from db import BaseDatos
from modelos.cliente import Cliente
from repositorios.repositorio_clientes import RepositorioClientes
from utilidades.excepciones import (
    ErrorDuplicado,
    ErrorNoEncontrado,
    ErrorValidacion,
)
from utilidades.validaciones import validar_campos_permitidos


class ServicioClientes:
    """Orquesta las operaciones de alta, consulta y modificación de clientes."""

    CAMPOS_ACTUALIZABLES = frozenset(
        {"documento", "nombre", "apellido", "telefono", "correo_electronico"}
    )
    MENSAJE_DOCUMENTO_DUPLICADO = "Ya existe un cliente con el documento indicado."

    def __init__(
        self,
        base_datos: BaseDatos,
        repositorio: RepositorioClientes | None = None,
    ) -> None:
        self._base_datos = base_datos
        self._repositorio = repositorio or RepositorioClientes(base_datos)

    def registrar(
        self,
        documento: str,
        nombre: str,
        apellido: str,
        telefono: str | None = None,
        correo_electronico: str | None = None,
    ) -> Cliente:
        """Registra un cliente nuevo."""
        cliente = Cliente(
            documento=documento,
            nombre=nombre,
            apellido=apellido,
            telefono=telefono,
            correo_electronico=correo_electronico,
        )

        try:
            with self._base_datos.transaccion():
                if (
                    self._repositorio.obtener_por_documento(cliente.documento)
                    is not None
                ):
                    raise ErrorValidacion(self.MENSAJE_DOCUMENTO_DUPLICADO)
                nuevo_id = self._repositorio.crear(cliente)
        except ErrorDuplicado as exc:
            raise ErrorValidacion(self.MENSAJE_DOCUMENTO_DUPLICADO) from exc

        return replace(cliente, id=nuevo_id)

    def obtener(self, cliente_id: int) -> Cliente:
        """Obtiene un cliente o lanza ErrorNoEncontrado."""
        return self._obtener_o_error(cliente_id)

    def listar(self, incluir_inactivos: bool = False) -> list[Cliente]:
        """Lista clientes, excluyendo los inactivos por defecto."""
        return self._repositorio.listar(incluir_inactivos=incluir_inactivos)

    def modificar(self, cliente_id: int, **cambios) -> Cliente:
        """Modifica campos permitidos de un cliente existente."""
        validar_campos_permitidos(cambios, self.CAMPOS_ACTUALIZABLES)

        try:
            with self._base_datos.transaccion():
                actual = self._obtener_o_error(cliente_id)
                actualizado = replace(actual, **cambios)

                if actualizado.documento != actual.documento:
                    existente = self._repositorio.obtener_por_documento(
                        actualizado.documento
                    )
                    if existente is not None and existente.id != actualizado.id:
                        raise ErrorValidacion(self.MENSAJE_DOCUMENTO_DUPLICADO)

                self._repositorio.actualizar(actualizado)
        except ErrorDuplicado as exc:
            raise ErrorValidacion(self.MENSAJE_DOCUMENTO_DUPLICADO) from exc

        return actualizado

    def cambiar_activo(self, cliente_id: int, activo: bool) -> Cliente:
        """Activa o desactiva lógicamente un cliente."""
        if not isinstance(activo, bool):
            raise TypeError("activo debe ser booleano.")

        with self._base_datos.transaccion():
            actual = self._obtener_o_error(cliente_id)
            self._repositorio.actualizar_activo(cliente_id, activo)

        return replace(actual, activo=activo)

    def dar_de_baja(self, cliente_id: int) -> Cliente:
        """Aplica baja lógica al cliente."""
        return self.cambiar_activo(cliente_id, False)

    def reactivar(self, cliente_id: int) -> Cliente:
        """Reactiva un cliente dado de baja."""
        return self.cambiar_activo(cliente_id, True)

    def _obtener_o_error(self, cliente_id: int) -> Cliente:
        cliente = self._repositorio.obtener_por_id(cliente_id)
        if cliente is None:
            raise ErrorNoEncontrado(f"No existe un cliente con id {cliente_id}.")
        return cliente
