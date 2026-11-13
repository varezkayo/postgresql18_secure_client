import getpass
import json
import sys
from pathlib import Path

import psycopg


def main():
    try:
        config_path = Path(__file__).with_name("config.json")
        with config_path.open(encoding="utf-8") as file:
            config = json.load(file)

        login = input("Логин: ")
        password = getpass.getpass("Пароль: ")

        # Передаём значения отдельно, не собираем строку подключения.
        with psycopg.connect(
            host=config["host"],
            port=config["port"],
            dbname=config["dbname"],
            user=login,
            password=password,
            connect_timeout=5,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT VERSION();")
                print(cursor.fetchone()[0])
        return 0
    except psycopg.Error:
        print("Ошибка подключения или выполнения запроса.", file=sys.stderr)
        return 1
    except (OSError, ValueError, KeyError):
        print("Ошибка чтения config.json.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
