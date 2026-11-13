import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import psycopg


def write_log(message, error=False):
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S} {message}"
    print(line, file=sys.stderr if error else sys.stdout, flush=True)
    log_file = os.getenv("LOG_FILE")
    if log_file:
        try:
            with open(log_file, "a", encoding="utf-8") as file:
                file.write(line + "\n")
        except OSError:
            print("Не удалось записать лог в файл.", file=sys.stderr, flush=True)


def check_database():
    try:
        with Path(__file__).with_name("config.json").open(encoding="utf-8") as file:
            config = json.load(file)

        with psycopg.connect(
            host=config["host"],
            port=config["port"],
            dbname=config["dbname"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            connect_timeout=5,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT VERSION();")
                result = cursor.fetchone()
        # Любой ответ без ошибки выводим в stdout, даже если он необычный.
        write_log(f"Подключение успешно. Ответ: {result}")
    except psycopg.Error:
        write_log("Ошибка подключения или выполнения запроса.", error=True)
    except (OSError, ValueError, KeyError):
        write_log("Ошибка настроек подключения.", error=True)


def main():
    try:
        interval = int(os.getenv("CHECK_INTERVAL", "300"))
        if interval <= 0:
            raise ValueError
        if not os.environ["DB_USER"] or not os.environ["DB_PASSWORD"]:
            raise ValueError
    except (ValueError, KeyError):
        write_log("Задайте DB_USER, DB_PASSWORD и положительный CHECK_INTERVAL.", error=True)
        return 1

    try:
        while True:
            started = time.monotonic()
            try:
                # Отдельный процесс позволяет прервать всю проверку при зависании сети.
                subprocess.run([sys.executable, __file__, "--check"], timeout=15, check=False)
            except subprocess.TimeoutExpired:
                write_log("Превышено время проверки: 15 секунд.", error=True)
            time.sleep(max(0, interval - (time.monotonic() - started)))
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--check"]:
        check_database()
    else:
        sys.exit(main())
