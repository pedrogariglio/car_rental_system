"""Reglas de negocio de reservas y disponibilidad."""

from dataclasses import replace
from datetime import datetime
from decimal import Decimal

from db import BaseDatos
from modelos.estados import EstadoReserva, EstadoVehiculo
from modelos.reserva import Reserva
from modelos.vehiculo import Vehiculo
from repositorios.repositorio_alquileres import RepositorioAlquileres
from repositorios.repositorio_clientes import RepositorioClientes
from repositorios.repositorio_reservas import RepositorioReservas
from repositorios.repositorio_vehiculos import RepositorioVehiculos
from servicios.facturacion import calcular_importe_estimado
from utilidades.excepciones import ErrorNoEncontrado, ErrorValidacion
from utilidades.validaciones import (
    validar_campos_permitidos,
    validar_rango_fechas,
)


class ServicioReservas:
    """Orquesta la creación, modificación, cancelación y disponibilidad."""

    CAMPOS_ACTUALIZABLES = frozenset(
        {
            "fecha_hora_retiro_prevista",
            "fecha_hora_devolucion_prevista",
            "tarifa_diaria_acordada",
        }
    )
    MENSAJE_NO_DISPONIBLE = (
        "El vehículo no está disponible para el período solicitado."
    )

    def __init__(
        self,
        base_datos: BaseDatos,
        repositorio_reservas: RepositorioReservas | None = None,
        repositorio_vehiculos: RepositorioVehiculos | None = None,
        repositorio_clientes: RepositorioClientes | None = None,
        repositorio_alquileres: RepositorioAlquileres | None = None,
    ) -> None:
        self._base_datos = base_datos
        self._reservas = repositorio_reservas or RepositorioReservas(base_datos)
        self._vehiculos = repositorio_vehiculos or RepositorioVehiculos(
            base_datos
        )
        self._clientes = repositorio_clientes or RepositorioClientes(base_datos)
        self._alquileres = repositorio_alquileres or RepositorioAlquileres(
            base_datos
        )

    def crear(
        self,
        cliente_id: int,
        vehiculo_id: int,
        fecha_hora_retiro_prevista: datetime,
        fecha_hora_devolucion_prevista: datetime,
        tarifa_diaria_acordada: Decimal | None = None,
    ) -> Reserva:
        """Crea una reserva confirmada si el vehículo está disponible."""
        with self._base_datos.transaccion():
            cliente = self._clientes.obtener_por_id(cliente_id)
            if cliente is None:
                raise ErrorNoEncontrado(
                    f"No existe un cliente con id {cliente_id}."
                )
            if not cliente.activo:
                raise ErrorValidacion(
                    "El cliente está inactivo y no puede generar reservas."
                )

            vehiculo = self._vehiculos.obtener_por_id(
                vehiculo_id, for_update=True
            )
            if vehiculo is None:
                raise ErrorNoEncontrado(
                    f"No existe un vehículo con id {vehiculo_id}."
                )

            tarifa = (
                tarifa_diaria_acordada
                if tarifa_diaria_acordada is not None
                else vehiculo.tarifa_diaria
            )
            importe_estimado = calcular_importe_estimado(
                tarifa,
                fecha_hora_retiro_prevista,
                fecha_hora_devolucion_prevista,
            )
            reserva = Reserva(
                cliente_id=cliente_id,
                vehiculo_id=vehiculo_id,
                fecha_hora_retiro_prevista=fecha_hora_retiro_prevista,
                fecha_hora_devolucion_prevista=fecha_hora_devolucion_prevista,
                tarifa_diaria_acordada=tarifa,
                importe_estimado=importe_estimado,
            )

            self._verificar_disponibilidad(
                vehiculo,
                reserva.fecha_hora_retiro_prevista,
                reserva.fecha_hora_devolucion_prevista,
            )
            nuevo_id = self._reservas.crear(reserva)

        return replace(reserva, id=nuevo_id)

    def obtener(self, reserva_id: int) -> Reserva:
        """Obtiene una reserva o lanza ErrorNoEncontrado."""
        return self._obtener_o_error(reserva_id)

    def listar(
        self,
        cliente_id: int | None = None,
        vehiculo_id: int | None = None,
    ) -> list[Reserva]:
        """Lista reservas con filtros opcionales."""
        return self._reservas.listar(
            cliente_id=cliente_id, vehiculo_id=vehiculo_id
        )

    def modificar(self, reserva_id: int, **cambios) -> Reserva:
        """Modifica fechas o tarifa de una reserva confirmada sin alquiler."""
        validar_campos_permitidos(cambios, self.CAMPOS_ACTUALIZABLES)

        with self._base_datos.transaccion():
            referencia = self._obtener_o_error(reserva_id)
            vehiculo = self._vehiculos.obtener_por_id(
                referencia.vehiculo_id, for_update=True
            )
            if vehiculo is None:
                raise ErrorNoEncontrado(
                    f"No existe un vehículo con id {referencia.vehiculo_id}."
                )

            actual = self._obtener_o_error(reserva_id, for_update=True)
            self._verificar_reserva_modificable(actual)

            retiro = cambios.get(
                "fecha_hora_retiro_prevista",
                actual.fecha_hora_retiro_prevista,
            )
            devolucion = cambios.get(
                "fecha_hora_devolucion_prevista",
                actual.fecha_hora_devolucion_prevista,
            )
            tarifa = cambios.get(
                "tarifa_diaria_acordada", actual.tarifa_diaria_acordada
            )
            importe_estimado = calcular_importe_estimado(
                tarifa, retiro, devolucion
            )

            actualizado = replace(
                actual,
                **cambios,
                importe_estimado=importe_estimado,
            )
            self._verificar_disponibilidad(
                vehiculo,
                actualizado.fecha_hora_retiro_prevista,
                actualizado.fecha_hora_devolucion_prevista,
                excluir_reserva_id=reserva_id,
            )
            self._reservas.actualizar(actualizado)

        return actualizado

    def cancelar(self, reserva_id: int) -> Reserva:
        """Cancela una reserva confirmada que no tenga alquiler asociado."""
        with self._base_datos.transaccion():
            referencia = self._obtener_o_error(reserva_id)
            self._vehiculos.obtener_por_id(
                referencia.vehiculo_id, for_update=True
            )

            actual = self._obtener_o_error(reserva_id, for_update=True)

            if actual.estado is not EstadoReserva.CONFIRMADA:
                raise ErrorValidacion(
                    "Solo se pueden cancelar reservas confirmadas."
                )
            if self._alquileres.existe_para_reserva(
                reserva_id, for_update=True
            ):
                raise ErrorValidacion(
                    "La reserva tiene un alquiler asociado y no puede cancelarse."
                )

            self._reservas.actualizar_estado(
                reserva_id, EstadoReserva.CANCELADA
            )

        return replace(actual, estado=EstadoReserva.CANCELADA)

    def consultar_disponibilidad(
        self,
        vehiculo_id: int,
        fecha_hora_retiro: datetime,
        fecha_hora_devolucion: datetime,
    ) -> bool:
        """Indica si el vehículo está disponible para el intervalo solicitado."""
        with self._base_datos.transaccion():
            vehiculo = self._vehiculos.obtener_por_id(vehiculo_id)
            if vehiculo is None:
                raise ErrorNoEncontrado(
                    f"No existe un vehículo con id {vehiculo_id}."
                )

            try:
                self._verificar_disponibilidad(
                    vehiculo,
                    fecha_hora_retiro,
                    fecha_hora_devolucion,
                    for_update=False,
                )
            except ErrorValidacion:
                return False

        return True

    def _verificar_disponibilidad(
        self,
        vehiculo: Vehiculo,
        fecha_hora_retiro: datetime,
        fecha_hora_devolucion: datetime,
        excluir_reserva_id: int | None = None,
        *,
        for_update: bool = True,
    ) -> None:
        validar_rango_fechas(
            fecha_hora_retiro,
            fecha_hora_devolucion,
            nombre_inicio="fecha_hora_retiro",
            nombre_fin="fecha_hora_devolucion",
        )

        if vehiculo.estado in (
            EstadoVehiculo.BAJA,
            EstadoVehiculo.MANTENIMIENTO,
        ):
            raise ErrorValidacion(
                "El vehículo no está disponible por su estado operativo."
            )

        if self._alquileres.existe_en_curso_solapado(
            vehiculo.id,
            fecha_hora_devolucion,
            for_update=for_update,
        ):
            raise ErrorValidacion(
                "El vehículo tiene un alquiler en curso en el período solicitado."
            )

        if self._reservas.buscar_solapadas(
            vehiculo.id,
            fecha_hora_retiro,
            fecha_hora_devolucion,
            excluir_reserva_id=excluir_reserva_id,
            for_update=for_update,
        ):
            raise ErrorValidacion(self.MENSAJE_NO_DISPONIBLE)

    def _verificar_reserva_modificable(self, reserva: Reserva) -> None:
        if reserva.estado is not EstadoReserva.CONFIRMADA:
            raise ErrorValidacion(
                "Solo se pueden modificar reservas confirmadas."
            )
        if self._alquileres.existe_para_reserva(
            reserva.id, for_update=True
        ):
            raise ErrorValidacion(
                "La reserva tiene un alquiler asociado y no puede modificarse."
            )

    def _obtener_o_error(
        self, reserva_id: int, *, for_update: bool = False
    ) -> Reserva:
        reserva = self._reservas.obtener_por_id(
            reserva_id, for_update=for_update
        )
        if reserva is None:
            raise ErrorNoEncontrado(
                f"No existe una reserva con id {reserva_id}."
            )
        return reserva
