# Лаба 2. Проверка доступности PostgreSQL

Цель: на основе первой работы сделать сервис, который раз в 5 минут выполняет `SELECT VERSION();`.

Нужен Docker Desktop. Команды выполняются из папки работы в PowerShell.

```powershell
$env:PINGER_ENV_FILE = "demo.env"
docker compose build
docker compose up -d --wait db
docker compose up -d pinger
docker compose logs -f pinger
```

Собираются образы `lab2-postgres:18` и `lab2-pinger:1.0`.
Путь к Env-файлу передаётся через `PINGER_ENV_FILE` в Compose.
В `demo.env` заданы учебные логин и пароль, интервал `CHECK_INTERVAL=300` секунд
и путь дублирования логов `LOG_FILE=/logs/pinger.log`.
Чтобы не писать в файл, удалите строку `LOG_FILE`.

Программа читает адрес базы из `config.json`, а логин и пароль — из окружения.
Успешный и необычный ответ попадает в stdout, ошибка — в stderr.
Каждая проверка ограничена 15 секундами. После ошибки выполняется следующая проверка.
Копия логов сохраняется на компьютере в `logs/pinger.log`.

Проверка восстановления после ошибки:

```powershell
docker compose down
docker compose up -d pinger
docker compose logs -f pinger
```

Дождитесь сообщения об ошибке и нажмите Ctrl+C — это закроет просмотр логов.
Затем запустите базу:

```powershell
docker compose up -d --wait db
docker compose logs -f pinger
```

При следующей проверке появится успешный ответ. Для быстрой демонстрации можно
временно заменить `CHECK_INTERVAL=300` на `CHECK_INTERVAL=10` в `demo.env`
перед запуском pinger. После изменения Env-файла пересоздайте контейнер:
`docker compose up -d --force-recreate pinger`.

Остановка: `docker compose down`.
