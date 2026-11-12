"""Reglas de negocio de alquileres y devoluciones."""

from dataclasses import replace
from datetime import datetime

from db import BaseDatos
from modelos.alquiler import Alquiler
from modelos.estados import EstadoAlquiler, EstadoReserva, EstadoVehiculo
from repositorios.repositorio_alquileres import RepositorioAlquileres
from repositorios.repositorio_reservas import RepositorioReservas
from repositorios.repositorio_vehiculos import RepositorioVehiculos
from servicios.facturacion import calcular_facturacion
from utilidades.excepciones import (
    ErrorDuplicado,
    ErrorNoEncontrado,
    ErrorValidacion,
)


class ServicioAlquileres:
    """Orquesta el inicio y cierre de alquileres asociados a reservas."""

    MENSAJE_ALQUILER_DUPLICADO = (
        "La reserva ya tiene un alquiler asociado."
    )

    def __init__(
        self,
        base_datos: BaseDatos,
        repositorio_alquileres: RepositorioAlquileres | None = None,
        repositorio_reservas: RepositorioReservas | None = None,
        repositorio_vehiculos: RepositorioVehiculos | None = None,
    ) -> None:
        self._base_datos = base_datos
        self._alquileres = repositorio_alquileres or RepositorioAlquileres(
            base_datos
        )
        self._reservas = repositorio_reservas or RepositorioReservas(
            base_datos
        )
        self._vehiculos = repositorio_vehiculos or RepositorioVehiculos(
            base_datos
        )

    def iniciar(
        self, reserva_id: int, fecha_hora_retiro_real: datetime
    ) -> Alquiler:
        """Inicia un alquiler sobre una reserva confirmada."""
        with self._base_datos.transaccion():
            reserva_referencia = self._reservas.obtener_por_id(reserva_id)
            if reserva_referencia is None:
                raise ErrorNoEncontrado(
                    f"No existe una reserva con id {reserva_id}."
                )

            vehiculo = self._vehiculos.obtener_por_id(
                reserva_referencia.vehiculo_id, for_update=True
            )
            if vehiculo is None:
                raise ErrorNoEncontrado(
                    "No existe el vehículo asociado a la reserva."
                )

            reserva = self._reservas.obtener_por_id(
                reserva_id, for_update=True
            )
            if reserva is None:
                raise ErrorNoEncontrado(
                    f"No existe una reserva con id {reserva_id}."
                )
            if reserva.estado is not EstadoReserva.CONFIRMADA:
                raise ErrorValidacion(
                    "Solo se puede iniciar un alquiler de una reserva confirmada."
                )
            if vehiculo.estado in (
                EstadoVehiculo.BAJA,
                EstadoVehiculo.MANTENIMIENTO,
            ):
                raise ErrorValidacion(
                    "El vehículo no está disponible por su estado operativo."
                )
            if self._alquileres.existe_para_reserva(
                reserva_id, for_update=True
            ):
                raise ErrorValidacion(self.MENSAJE_ALQUILER_DUPLICADO)
            if self._alquileres.existe_en_curso_para_vehiculo(
                vehiculo.id, for_update=True
            ):
                raise ErrorValidacion(
                    "El vehículo ya tiene un alquiler en curso."
                )

            alquiler = Alquiler(
                reserva_id=reserva_id,
                fecha_hora_retiro_real=fecha_hora_retiro_real,
            )

            try:
                nuevo_id = self._alquileres.crear(alquiler)
            except ErrorDuplicado as exc:
                raise ErrorValidacion(
                    self.MENSAJE_ALQUILER_DUPLICADO
                ) from exc

            self._vehiculos.actualizar_estado(
                vehiculo.id, EstadoVehiculo.ALQUILADO
            )

        return replace(alquiler, id=nuevo_id)

    def cerrar(
        self, alquiler_id: int, fecha_hora_devolucion_real: datetime
    ) -> Alquiler:
        """Registra la devolución y cierra el alquiler."""
        with self._base_datos.transaccion():
            alquiler_referencia = self._alquileres.obtener_por_id(alquiler_id)
            if alquiler_referencia is None:
                raise ErrorNoEncontrado(
                    f"No existe un alquiler con id {alquiler_id}."
                )

            reserva_referencia = self._reservas.obtener_por_id(
                alquiler_referencia.reserva_id
            )
            if reserva_referencia is None:
                raise ErrorNoEncontrado(
                    "No existe la reserva asociada al alquiler."
                )

            vehiculo = self._vehiculos.obtener_por_id(
                reserva_referencia.vehiculo_id, for_update=True
            )
            if vehiculo is None:
                raise ErrorNoEncontrado(
                    "No existe el vehículo asociado al alquiler."
                )

            reserva = self._reservas.obtener_por_id(
                alquiler_referencia.reserva_id, for_update=True
            )
            if reserva is None:
                raise ErrorNoEncontrado(
                    "No existe la reserva asociada al alquiler."
                )

            alquiler = self._alquileres.obtener_por_id(
                alquiler_id, for_update=True
            )
            if alquiler is None:
                raise ErrorNoEncontrado(
                    f"No existe un alquiler con id {alquiler_id}."
                )
            if alquiler.estado is not EstadoAlquiler.EN_CURSO:
                raise ErrorValidacion(
                    "Solo se pueden cerrar alquileres en curso."
                )

            resultado = calcular_facturacion(
                reserva.tarifa_diaria_acordada,
                reserva.fecha_hora_retiro_prevista,
                reserva.fecha_hora_devolucion_prevista,
                alquiler.fecha_hora_retiro_real,
                fecha_hora_devolucion_real,
            )

            actualizado = replace(
                alquiler,
                fecha_hora_devolucion_real=fecha_hora_devolucion_real,
                importe_base=resultado.importe_base,
                recargo_demora=resultado.recargo_demora,
                importe_final=resultado.importe_final,
                estado=EstadoAlquiler.FINALIZADO,
            )

            self._alquileres.actualizar_cierre(actualizado)
            self._reservas.actualizar_estado(
                reserva.id, EstadoReserva.COMPLETADA
            )
            if vehiculo.estado is EstadoVehiculo.ALQUILADO:
                self._vehiculos.actualizar_estado(
                    vehiculo.id, EstadoVehiculo.DISPONIBLE
                )

        return actualizado

    def obtener(self, alquiler_id: int) -> Alquiler:
        """Obtiene un alquiler o lanza ErrorNoEncontrado."""
        alquiler = self._alquileres.obtener_por_id(alquiler_id)
        if alquiler is None:
            raise ErrorNoEncontrado(
                f"No existe un alquiler con id {alquiler_id}."
            )
        return alquiler

    def obtener_por_reserva(self, reserva_id: int) -> Alquiler | None:
        """Obtiene el alquiler de una reserva, si existe."""
        return self._alquileres.obtener_por_reserva_id(reserva_id)

    def listar(
        self,
        cliente_id: int | None = None,
        vehiculo_id: int | None = None,
    ) -> list[Alquiler]:
        """Lista alquileres con filtros opcionales."""
        return self._alquileres.listar(
            cliente_id=cliente_id, vehiculo_id=vehiculo_id
        )
