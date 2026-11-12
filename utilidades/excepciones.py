"""Excepciones propias de la aplicación."""


class ErrorValidacion(ValueError):
    """Se lanza cuando un dato o una regla de negocio no es válido."""


class ErrorNoEncontrado(ErrorValidacion):
    """Se lanza cuando no existe el registro solicitado."""


class ErrorConfiguracion(Exception):
    """Se lanza cuando falta o es inválida una variable de configuración."""


class ErrorBaseDatos(Exception):
    """Se lanza cuando falla una operación contra MySQL."""


class ErrorDuplicado(ErrorBaseDatos):
    """Se lanza cuando una restricción UNIQUE impide la operación."""
