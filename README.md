# Задание 2. Проверка PostgreSQL

```powershell
docker compose up --build -d
docker compose logs -f pinger
```

Сервис выполняет `SELECT VERSION()` сразу и затем раз в 300 секунд. Успех и необычный ответ идут в stdout, сбой в stderr. `demo.env` содержит учебные логин, пароль, интервал и необязательный путь к журналу. Порт БД наружу не открыт.

Показ сбоя и восстановления: один раз дождитесь успешного подключения, чтобы база успела создаться. Затем выполните `docker compose stop pinger db` и `docker compose run --rm --no-deps -e POLL_SECONDS=15 pinger`. Сразу после первой ошибки запустите `docker compose up -d db` во втором терминале. Следующий опрос должен быть успешным. Завершите показ через Ctrl+C и `docker compose down`.
