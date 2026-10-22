"""Seminar 1: PostgreSQL 18 connection using secure keyword arguments."""

from __future__ import annotations

import getpass
import sys
import tomllib
from pathlib import Path
from typing import Any

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.toml"
ALLOWED_KEYS = {"host", "port", "dbname", "connect_timeout", "sslmode"}


class ConfigurationError(ValueError):
    """Invalid or unexpected connection configuration."""


def load_settings(path: Path = CONFIG_PATH) -> dict[str, Any]:
    """Load and strictly validate the allowlisted TOML server settings."""
    try:
        with path.open("rb") as stream:
            config = tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ConfigurationError(f"Не удалось прочитать {path.name}: {exc}") from exc

    if set(config) != {"database"} or not isinstance(config["database"], dict):
        raise ConfigurationError("Файл должен содержать только раздел [database].")
    settings = config["database"]
    if set(settings) != ALLOWED_KEYS:
        raise ConfigurationError(
            f"Недопустимые или отсутствующие параметры подключения. Разрешены: {', '.join(sorted(ALLOWED_KEYS))}."
        )
    if not isinstance(settings["host"], str) or not settings["host"].strip():
        raise ConfigurationError("host должен быть непустой строкой.")
    if not isinstance(settings["dbname"], str) or not settings["dbname"].strip():
        raise ConfigurationError("dbname должен быть непустой строкой.")
    if type(settings["port"]) is not int or not 1 <= settings["port"] <= 65535:
        raise ConfigurationError("port должен быть целым числом от 1 до 65535.")
    if type(settings["connect_timeout"]) is not int or not 1 <= settings["connect_timeout"] <= 60:
        raise ConfigurationError("connect_timeout должен быть целым числом от 1 до 60.")
    if not isinstance(settings["sslmode"], str) or settings["sslmode"] not in {
        "disable", "require", "verify-full"
    }:
        raise ConfigurationError("Недопустимое значение sslmode.")
    return settings.copy()


def connection_parameters(settings: dict[str, Any], username: str, password: str) -> dict[str, Any]:
    """Keep login/password as *values*, never concatenate them into conninfo.

    In particular, the username "seminar_user host=otherhost" cannot add
    an extra `host` option: it remains a single `user` keyword argument.
    """
    if not username or "\x00" in username or "\n" in username or "\r" in username:
        raise ValueError("Логин не должен быть пустым или содержать управляющие символы.")
    if not password or "\x00" in password:
        raise ValueError("Пароль не должен быть пустым или содержать NUL-символ.")
    return {
        "host": settings["host"],
        "port": settings["port"],
        "dbname": settings["dbname"],
        "connect_timeout": settings["connect_timeout"],
        "sslmode": settings["sslmode"],
        "user": username,
        "password": password,
    }


def main() -> int:
    try:
        settings = load_settings()
        print("=== Подключение к PostgreSQL 18 ===")
        print(f"Сервер: {settings['host']}:{settings['port']}")
        print(f"База данных: {settings['dbname']}")
        username = input("Логин: ")
        password = getpass.getpass("Пароль (ввод скрыт): ")
        params = connection_parameters(settings, username, password)
    except (ConfigurationError, ValueError) as exc:
        print(f"Ошибка конфигурации/ввода: {exc}", file=sys.stderr)
        return 1
    except (KeyboardInterrupt, EOFError):
        print("\nВвод прерван.")
        return 130

    try:
        import psycopg

        # psycopg itself encodes keyword values safely as libpq parameters.
        # We never create a connection string from the user's raw input.
        with psycopg.connect(**params) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT VERSION();")
                version = cursor.fetchone()[0]
                cursor.execute("SELECT current_user, current_database();")
                who, db = cursor.fetchone()
        print("\nПодключение успешно!")
        print(f"Пользователь: {who}")
        print(f"База данных: {db}")
        print("\nРезультат SELECT VERSION():")
        print(version)
        return 0
    except ImportError:
        print("Не установлен psycopg. Выполните: python -m pip install -r requirements.txt", file=sys.stderr)
        return 1
    except psycopg.Error as exc:
        # No password, DSN, or connection params are printed here.
        print(f"Подключение или запрос не выполнены: {exc.__class__.__name__}", file=sys.stderr)
        print("Проверьте Docker, логин, пароль и config.toml.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
