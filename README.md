# Лаба 1. Подключение к PostgreSQL

Цель: подключиться к PostgreSQL 18 и выполнить `SELECT VERSION();`.

Нужны Docker Desktop и Python 3.10 или новее. Команды выполняются из папки работы.

```powershell
docker compose up -d --build --wait
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Логин: `student`. Пароль: `student_demo_password`. Это учебные значения.
При правильном вводе программа выводит версию PostgreSQL, при неверном — сообщение об ошибке.

Адрес, порт и имя базы читаются из `config.json` рядом с программой.
Логин и пароль вводятся с клавиатуры и передаются драйверу отдельными параметрами.
Поэтому ввод вроде `student host=other` останется логином, а не изменит адрес подключения.

База использует локаль `ru_RU.UTF-8` и аутентификацию SCRAM-SHA-256.
Пользователю выданы `CONNECT` к базе и `USAGE` к схеме `public`.

Остановка: `docker compose down`.
