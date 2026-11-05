# Задание 3. Книжный магазин

```powershell
docker compose build
docker compose up -d --wait db
docker compose run --rm app
```

Логин `bookshop_user`, учебный пароль — значение `BOOKSHOP_PASSWORD` из `db.env`. В меню есть просмотр с фильтрами, два вида обновления, одиночная и пакетная вставка, а также заказ вместе с его позициями.

В `sql/` находятся схема пяти таблиц, демоданные и права пользователя. `demo.env` задаёт путь к журналу приложения. Завершить: пункт `0`, затем `docker compose down`.
