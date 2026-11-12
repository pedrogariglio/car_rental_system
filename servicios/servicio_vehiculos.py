"""Reglas de negocio para la administración de vehículos."""

from dataclasses import replace
from decimal import Decimal

from db import BaseDatos
from modelos.estados import EstadoVehiculo
from modelos.vehiculo import Vehiculo
from repositorios.repositorio_vehiculos import RepositorioVehiculos
from utilidades.excepciones import (
    ErrorDuplicado,
    ErrorNoEncontrado,
    ErrorValidacion,
)
from utilidades.validaciones import validar_campos_permitidos, validar_enum


class ServicioVehiculos:
    """Orquesta las operaciones de alta, consulta y modificación de vehículos."""

    CAMPOS_ACTUALIZABLES = frozenset(
        {"patente", "marca", "modelo", "anio", "categoria", "tarifa_diaria"}
    )
    MENSAJE_PATENTE_DUPLICADA = "Ya existe un vehículo con la patente indicada."

    def __init__(
        self,
        base_datos: BaseDatos,
        repositorio: RepositorioVehiculos | None = None,
    ) -> None:
        self._base_datos = base_datos
        self._repositorio = repositorio or RepositorioVehiculos(base_datos)

    def registrar(
        self,
        patente: str,
        marca: str,
        modelo: str,
        anio: int,
        categoria: str,
        tarifa_diaria: Decimal,
    ) -> Vehiculo:
        """Registra un vehículo nuevo."""
        vehiculo = Vehiculo(
            patente=patente,
            marca=marca,
            modelo=modelo,
            anio=anio,
            categoria=categoria,
            tarifa_diaria=tarifa_diaria,
        )

        try:
            with self._base_datos.transaccion():
                if (
                    self._repositorio.obtener_por_patente(vehiculo.patente)
                    is not None
                ):
                    raise ErrorValidacion(self.MENSAJE_PATENTE_DUPLICADA)
                nuevo_id = self._repositorio.crear(vehiculo)
        except ErrorDuplicado as exc:
            raise ErrorValidacion(self.MENSAJE_PATENTE_DUPLICADA) from exc

        return replace(vehiculo, id=nuevo_id)

    def obtener(self, vehiculo_id: int) -> Vehiculo:
        """Obtiene un vehículo o lanza ErrorNoEncontrado."""
        return self._obtener_o_error(vehiculo_id)

    def listar(self, incluir_baja: bool = False) -> list[Vehiculo]:
        """Lista vehículos, excluyendo los dados de baja por defecto."""
        return self._repositorio.listar(incluir_baja=incluir_baja)

    def modificar(self, vehiculo_id: int, **cambios) -> Vehiculo:
        """Modifica campos permitidos de un vehículo existente."""
        validar_campos_permitidos(cambios, self.CAMPOS_ACTUALIZABLES)

        try:
            with self._base_datos.transaccion():
                actual = self._obtener_o_error(vehiculo_id)
                actualizado = replace(actual, **cambios)

                if actualizado.patente != actual.patente:
                    existente = self._repositorio.obtener_por_patente(
                        actualizado.patente
                    )
                    if existente is not None and existente.id != actualizado.id:
                        raise ErrorValidacion(self.MENSAJE_PATENTE_DUPLICADA)

                self._repositorio.actualizar(actualizado)
        except ErrorDuplicado as exc:
            raise ErrorValidacion(self.MENSAJE_PATENTE_DUPLICADA) from exc

        return actualizado

    def cambiar_estado(
        self, vehiculo_id: int, estado: EstadoVehiculo | str
    ) -> Vehiculo:
        """Cambia el estado operativo de un vehículo."""
        estado_validado = validar_enum(estado, EstadoVehiculo, "estado")

        with self._base_datos.transaccion():
            actual = self._obtener_o_error(vehiculo_id)
            self._repositorio.actualizar_estado(vehiculo_id, estado_validado)

        return replace(actual, estado=estado_validado)

    def dar_de_baja(self, vehiculo_id: int) -> Vehiculo:
        """Aplica baja lógica al vehículo."""
        return self.cambiar_estado(vehiculo_id, EstadoVehiculo.BAJA)

    def _obtener_o_error(self, vehiculo_id: int) -> Vehiculo:
        vehiculo = self._repositorio.obtener_por_id(vehiculo_id)
        if vehiculo is None:
            raise ErrorNoEncontrado(
                f"No existe un vehículo con id {vehiculo_id}."
            )
        return vehiculo
