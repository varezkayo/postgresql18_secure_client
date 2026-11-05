from pathlib import Path
import tomllib

import psycopg


def connect(user, password):
    with Path(__file__).with_name("config.toml").open("rb") as file:
        db = tomllib.load(file)["database"]
    if not user or not password or "\x00" in user + password:
        raise ValueError("Нужны логин и пароль без NUL.")
    return psycopg.connect(
        host=db["host"], port=db["port"], dbname=db["dbname"],
        connect_timeout=db["connect_timeout"], sslmode=db["sslmode"],
        options="-c statement_timeout=5000", user=user, password=password,
    )
