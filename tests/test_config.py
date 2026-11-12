"""Pruebas de lectura de configuración."""

import pytest

from config import obtener_config_bd, obtener_config_bd_pruebas
from utilidades.excepciones import ErrorConfiguracion


def test_config_bd_arma_parametros(monkeypatch) -> None:
    monkeypatch.setenv("DB_HOST", "127.0.0.1")
    monkeypatch.setenv("DB_PORT", "3307")
    monkeypatch.setenv("DB_USER", "root")
    monkeypatch.setenv("DB_PASSWORD", "secreto")
    monkeypatch.setenv("DB_NAME", "car_rental_system")

    assert obtener_config_bd() == {
        "host": "127.0.0.1",
        "port": 3307,
        "user": "root",
        "password": "secreto",
        "database": "car_rental_system",
    }


def test_config_bd_requiere_usuario(monkeypatch) -> None:
    monkeypatch.delenv("DB_USER", raising=False)
    monkeypatch.setenv("DB_NAME", "car_rental_system")

    with pytest.raises(ErrorConfiguracion):
        obtener_config_bd()


def test_config_bd_valida_puerto(monkeypatch) -> None:
    monkeypatch.setenv("DB_USER", "root")
    monkeypatch.setenv("DB_NAME", "car_rental_system")
    monkeypatch.setenv("DB_PORT", "no-es-numero")

    with pytest.raises(ErrorConfiguracion):
        obtener_config_bd()


def test_config_pruebas_requiere_nombre(monkeypatch) -> None:
    monkeypatch.delenv("DB_TEST_NAME", raising=False)
    monkeypatch.setenv("DB_USER", "root")

    with pytest.raises(ErrorConfiguracion):
        obtener_config_bd_pruebas()
