# Задание 1. Подключение к PostgreSQL 18

Нужны Docker Desktop и Python 3.11 или новее. Для первого запуска скопируйте `.env.example` в `.env` и задайте два разных локальных пароля.

```powershell
docker compose up -d --build --wait
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m src.app
```

Логин — `seminar_user`. Пароль — значение `APP_DB_PASSWORD` из `.env`. Клиент читает адрес из `config.toml`, подключается и показывает результат `SELECT VERSION()`. Логин и пароль передаются драйверу отдельно от остальных настроек.

PostgreSQL использует `ru_RU.UTF-8` и SCRAM-SHA-256; порт доступен только с этого компьютера. Остановить: `docker compose down`.
