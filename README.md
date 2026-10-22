# Задание №1. Безопасное подключение к PostgreSQL 18

[![Docker verification](https://github.com/varezkayo/postgresql18_secure_client/actions/workflows/verify.yml/badge.svg)](https://github.com/varezkayo/postgresql18_secure_client/actions/workflows/verify.yml)

Готовый проект для семинара: Docker + PostgreSQL 18 + Python 3.11+ + `psycopg` 3.

Исходники опубликованы в [публичном репозитории GitHub](https://github.com/varezkayo/postgresql18_secure_client). Состояние проверки от 22 октября 2026 года и оставшиеся шаги для сдачи приведены в [SUBMISSION.md](SUBMISSION.md). GitHub Actions выполняет сборку Docker и проверки настоящей БД; их результат доступен по значку выше. На локальном компьютере Docker Desktop и WSL пока не установлены.

## Соответствие требованиям

| Пункт задания | Реализация |
|---|---|
| PostgreSQL 18 в Docker | `Dockerfile`, `compose.yaml` |
| БД с `ru_RU.UTF-8` | Генерация локали в Dockerfile, `POSTGRES_INITDB_ARGS` |
| SCRAM-SHA-256 | `--auth-host`, `--auth-local`, `postgresql.conf` |
| Пользователь с доступом к БД и `public` | `docker/01-create-role.sh`: роль `seminar_user`, `CONNECT` к базе, `USAGE` к схеме |
| `SELECT VERSION();` | `src/app.py` |
| Настройки подключения рядом с приложением | `config.toml` в корне проекта рядом с запускаемым пакетом |
| Логин и пароль при запуске | `input()` и `getpass.getpass()` |
| Защита от добавления опций через ввод | `psycopg.connect(**params)` и белый список TOML-ключей |
| Файлы для публичного Git | исходники, Dockerfile, postgresql.conf, без паролей |
| Проверка работы | `tests/`, `docker/verify-db.sh` |

**Примечание по правам:** SQL не предусматривает `USAGE ON DATABASE`; для базы выдаётся право `CONNECT`, а для схемы `public` — `USAGE`.

## Быстрый запуск на Windows (PowerShell)

Требования: Docker Desktop с запущенным Linux-контейнерным движком, Docker Compose v2 и Python 3.11+.

1. Распакуйте проект.
2. Включите Docker Desktop и дождитесь запуска движка.
3. Откройте PowerShell из папки проекта.
4. Выполните:

   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\setup.ps1
   ```

   Скрипт создаёт или использует виртуальное окружение Python, устанавливает зафиксированные зависимости из `requirements.lock.txt`, запускает модульные тесты, **локально** создаёт `.env` со случайными паролями и собирает контейнер. Затем проверяет настройки БД и выполняет три интеграционных теста приложения. Пароли в журнал не выводятся.

   Если `python` или `py` указывает на неработающую заглушку Windows Store, укажите путь к настоящему Python:

   ```powershell
   .\setup.ps1 -PythonExecutable 'C:\path\to\python.exe'
   ```

   Для установки зависимостей и модульных тестов без Docker: `.\setup.ps1 -DependenciesOnly`. Этот режим не проверяет живую БД.

5. Для показа программы выполните:

   ```powershell
   .\run.ps1
   ```

   Введите **логин** `seminar_user` и **пароль** из значения `APP_DB_PASSWORD` в локальном `.env`. Откройте файл в редакторе и не показывайте его на записи или скриншотах. Пароль не выводится при вводе. При успешном подключении выведется версия сервера PostgreSQL.

Если PowerShell запрещён политикой организации, используйте ручной запуск ниже вместо отключения ограничений.

## Ручной запуск Windows / macOS / Linux

1. Создайте `.env` из `.env.example` и замените оба заполнителя разными случайными паролями.
2. Запустите БД:

   ```bash
   docker compose up -d --build --wait
   ```

3. Установите пакет в Python 3.11 или новее (желательно в виртуальном окружении):

   ```bash
   python -m pip install -r requirements.lock.txt
   ```

4. Проверьте базу и настройки:

   ```bash
   docker compose exec -T db /usr/local/bin/verify-db.sh
   ```

5. Запустите клиент (из корневой папки проекта):

   ```bash
   python -m src.app
   ```

   Имя пользователя — `seminar_user`, пароль — значение `APP_DB_PASSWORD` из локального `.env`.

6. Запустите юнит-тесты безопасности:

   ```bash
   python -m unittest discover -s tests -v
   ```

На Windows повторная полная проверка выполняется командой `.\verify.ps1`. Она завершится ошибкой, если контейнер недоступен, настройки БД не соответствуют заданию или хотя бы один тест не проходит. На macOS/Linux после проверки БД запустите отдельно `python -m unittest discover -s integration -v`, задав `APP_DB_PASSWORD` из локального `.env` в окружении процесса. Без этого значения интеграционные тесты явно пропускаются; это не успешная проверка живой БД.

## Как работает защита подключения

Параметры сервера (`host`, `port`, `dbname`, `connect_timeout`, `sslmode`) берутся **только** из `config.toml`. В нём запрещены дополнительные ключи, включая `options` и `service`. Имя пользователя и пароль вводятся отдельно. Вызов:

```python
psycopg.connect(
    host=settings["host"],
    port=settings["port"],
    dbname=settings["dbname"],
    connect_timeout=settings["connect_timeout"],
    sslmode=settings["sslmode"],
    user=username,
    password=password,
)
```

В реализации используются равнозначные именованные аргументы через словарь (`**params`). Никакой пользовательский текст не вставляется в единую connection string, поэтому строка вроде `seminar_user host=attacker.example` рассматривается как **одно имя пользователя**, а не как новая опция `host`.

Тесты намеренно подают подобные строки, проверяют неизменность настроек `host`/`port`/`dbname` и отклонение запрещённой опции в конфиге. Это проверка структуры аргументов, а не попытка реального подключения к атакующему серверу.

`sslmode=disable` применяется **только для локальной демонстрации**: порт Docker открыт на `127.0.0.1`. Для удалённой БД следует настроить TLS с проверкой сертификата и заменить `sslmode` на `verify-full`.

## Команды для показа преподавателю

```powershell
# Контейнер и состояние службы
docker compose ps

# Все проверки с настоящим PostgreSQL и приложением
.\verify.ps1

# Подробная проверка версии, локали, SCRAM и разрешений
docker compose exec -T db /usr/local/bin/verify-db.sh

# Тесты, включая инъекции в параметры подключения
.\.venv\Scripts\python.exe -m unittest discover -s tests -v

# Работа приложения
.\run.ps1
```

Для наглядного отрицательного теста: при запросе логина введите `seminar_user host=other.example` и любой пароль. Сервер отклонит вход, а адрес подключения **не изменится**.

## Вопросы для защиты

- **Почему SCRAM-SHA-256?** Сервер использует salt и криптографическую проверку знания пароля вместо передачи пароля в открытом виде; `password_encryption` задаёт формат сохранения новых паролей, а параметры HBA — метод сетевой аутентификации.
- **Почему нужен `USAGE` на схему?** Он разрешает обращаться к объектам внутри схемы при наличии необходимых прав на сами объекты. Право на подключение к БД задаётся отдельно (`CONNECT`).
- **Почему нельзя просто соединить строки конфига и введённые поля?** Так ввод пользователя может подменить/добавить опции libpq `host`, `port` и т.д. Именованные аргументы оставляют пользовательский ввод значением одного поля.
- **Что делает `getpass`?** Скрывает пароль во время ввода; это не шифрование канала и не полноценное хранилище секретов.
- **Почему пароль не указан в `config.toml`?** По условию приложения он должен приходить от пользователя, а публичный Git не должен содержать секреты.
- **Почему Docker volume привязан к `/var/lib/postgresql`, а не к `/var/lib/postgresql/data`?** Официальный образ PostgreSQL 18 использует `/var/lib/postgresql/18/docker` внутри этой директории.
- **Почему после изменения init.sh пользователь не изменился?** Инициализационные скрипты выполняются только при **первом создании пустого тома**.

## Частые проблемы

- `Cannot connect to Docker daemon`: сначала запустите Docker Desktop.
- `Port is already allocated`: порт `5432` уже занят; освободите порт или согласованно измените `compose.yaml` и `config.toml`.
- `password authentication failed`: введите пароль `APP_DB_PASSWORD` из `.env` для пользователя `seminar_user`. Если меняли `.env` **после** первой инициализации, пароль в базе не обновится автоматически.
- `locale ru_RU.UTF-8 is not supported`: убедитесь, что образ **собран из Dockerfile** (`docker compose up --build`), а не запущен напрямую из `postgres:18`.
- `No module named psycopg`: установите зависимости через Python из того же окружения, в котором запускаете программу.

Не используйте `docker compose down -v`, если в томе есть важные данные: эта команда **удаляет данные**.

## Публикация в GitHub

Откройте терминал из папки проекта и создайте **новый публичный репозиторий** в GitHub. Затем:

```bash
git init
git add .
git commit -m "PostgreSQL 18 seminar: secure Python client"
git branch -M main
git remote add origin https://github.com/USERNAME/REPOSITORY.git
git push -u origin main
```

Перед отправкой убедитесь, что `.env` и реальные пароли отсутствуют в `git status` / `git ls-files`. В Git должны быть `Dockerfile`, `compose.yaml`, `docker/postgresql.conf`, `config.toml`, исходный код и тесты.
