# Задание 2. Проверка PostgreSQL

```powershell
docker compose up --build -d
docker compose logs -f pinger
```

Сервис выполняет `SELECT VERSION()` сразу и затем раз в 300 секунд. Успех и необычный ответ идут в stdout, сбой в stderr. `demo.env` содержит учебные логин, пароль, интервал и необязательный путь к журналу. Порт БД наружу не открыт.

Показ сбоя и восстановления: в первом терминале выполните `docker compose stop pinger db`, затем `docker compose run --rm --no-deps -e POLL_SECONDS=5 pinger`. После первой ошибки во втором терминале выполните `docker compose up -d db` и дождитесь успешной проверки в первом. Завершите показ через Ctrl+C и `docker compose down`.
