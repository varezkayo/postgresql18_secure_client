import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from datetime import datetime

import psycopg

from db import connect


def log(message, error=False):
    line = f"{datetime.now().astimezone().isoformat(timespec='seconds')} {message}"
    print(line, file=sys.stderr if error else sys.stdout, flush=True)
    path = os.getenv("LOG_FILE")
    if path:
        try:
            with open(path, "a", encoding="utf-8") as file:
                print(line, file=file)
        except OSError:
            print("Не удалось записать лог в файл.", file=sys.stderr, flush=True)


def read_version():
    try:
        with connect(os.environ["APP_DB_USER"], os.environ["APP_DB_PASSWORD"]) as conn:
            result = conn.execute("SELECT VERSION();").fetchone()
        print(json.dumps(result[0] if result else None, ensure_ascii=True))
        return 0
    except (psycopg.Error, KeyError, ValueError, OSError):
        return 1


def poll():
    try:
        # Лимит на всю попытку, включая зависший после подключения обмен.
        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--once"],
            capture_output=True, text=True, encoding="utf-8", timeout=10,
        )
        if result.returncode:
            log("Не удалось подключиться или получить версию.", error=True)
            return
        version = json.loads(result.stdout)
        if isinstance(version, str) and re.match(r"^PostgreSQL 18(?:\.|\s|$)", version):
            log(f"Подключение успешно: {version}")
        else:
            log(f"Необычный ответ SELECT VERSION(): {version!r}")
    except subprocess.TimeoutExpired:
        log("Истекло время ожидания PostgreSQL.", error=True)
    except (OSError, ValueError):
        log("Не удалось выполнить проверку.", error=True)


def main():
    try:
        interval = int(os.getenv("POLL_SECONDS", "300"))
        if interval < 1:
            raise ValueError
    except ValueError:
        log("POLL_SECONDS должен быть целым числом больше нуля.", error=True)
        return 1

    try:
        while True:
            start = time.monotonic()
            poll()
            time.sleep(max(0, interval - (time.monotonic() - start)))
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(read_version() if sys.argv[1:] == ["--once"] else main())
