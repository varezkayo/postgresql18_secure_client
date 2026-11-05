import getpass
import os
import sys
from decimal import Decimal, InvalidOperation

import psycopg
from psycopg import sql

from db import connect

TABLES = {
    "authors": {"name": str},
    "books": {"author_id": int, "title": str, "price": Decimal},
    "customers": {"name": str, "email": str},
    "orders": {"customer_id": int, "status": str},
    "order_items": {"order_id": int, "book_id": int, "quantity": int},
}


def log(message, error=None):
    print(message, file=sys.stderr if error else sys.stdout, flush=True)
    path = os.getenv("LOG_FILE")
    if path:
        try:
            with open(path, "a", encoding="utf-8") as file:
                print(message, file=file)
                if error:
                    print(str(error), file=file)
        except OSError:
            print("Не удалось записать лог в файл.", file=sys.stderr)


def choose(prompt, options):
    answer = input(f"{prompt} ({', '.join(options)}): ").strip()
    if answer not in options:
        raise ValueError("Такого пункта или поля нет.")
    return answer


def value(prompt, kind):
    raw = input(f"{prompt}: ").strip()
    if not raw:
        raise ValueError("Значение не может быть пустым.")
    try:
        result = kind(raw)
        if isinstance(result, Decimal) and not result.is_finite():
            raise ValueError
        return result
    except (ValueError, InvalidOperation):
        raise ValueError("Проверьте формат числа.") from None


def count(prompt, minimum=1, maximum=50):
    n = value(prompt, int)
    if not minimum <= n <= maximum:
        raise ValueError(f"Введите число от {minimum} до {maximum}.")
    return n


def fields(table, include_id=False):
    return {"id": int, **TABLES[table]} if include_id else TABLES[table]


def read_row(table, skip=()):
    return {column: value(column, kind) for column, kind in fields(table).items()
            if column not in skip}


def select_rows(conn):
    table = choose("Таблица", TABLES)
    columns = fields(table, include_id=True)
    terms, params = [], []
    for _ in range(count("Число условий AND (0 — все записи)", 0, len(columns))):
        column = choose("Поле фильтра", columns)
        terms.append(sql.SQL("{} = %s").format(sql.Identifier(column)))
        params.append(value(column, columns[column]))
    query = sql.SQL("SELECT * FROM {}").format(sql.Identifier(table))
    if terms:
        query += sql.SQL(" WHERE ") + sql.SQL(" AND ").join(terms)
    with conn.transaction():
        rows = conn.execute(query + sql.SQL(" ORDER BY id"), params).fetchall()
    print(" | ".join(columns))
    for row in rows:
        print(" | ".join(map(str, row)))
    log(f"Запрос выполнен. Строк: {len(rows)}.")


def update_one(conn):
    table = choose("Таблица", TABLES)
    columns = fields(table)
    row_id = value("id записи", int)
    changes = {}
    for _ in range(count("Сколько полей изменить", 1, len(columns))):
        column = choose("Изменяемое поле", [name for name in columns if name not in changes])
        changes[column] = value(column, columns[column])
    assignments = sql.SQL(", ").join(
        sql.SQL("{} = %s").format(sql.Identifier(column)) for column in changes
    )
    query = sql.SQL("UPDATE {} SET {} WHERE id = %s").format(sql.Identifier(table), assignments)
    with conn.transaction():
        updated = conn.execute(query, [*changes.values(), row_id]).rowcount
    log(f"Обновлено строк: {updated}.")


def update_many(conn):
    table = choose("Таблица", TABLES)
    column = choose("Изменяемое поле", fields(table))
    new_value = value(column, fields(table)[column])
    columns = fields(table, include_id=True)
    key = choose("Поле фильтра", columns)
    values = [value(key, columns[key]) for _ in range(count("Сколько значений фильтра"))]
    query = sql.SQL("UPDATE {} SET {} = %s WHERE {} = ANY(%s)").format(
        sql.Identifier(table), sql.Identifier(column), sql.Identifier(key)
    )
    with conn.transaction():
        updated = conn.execute(query, (new_value, values)).rowcount
    log(f"Обновлено строк: {updated}.")


def insert_rows(conn, table, rows):
    columns = list(rows[0])
    values = sql.SQL("({})").format(sql.SQL(", ").join([sql.Placeholder()] * len(columns)))
    query = sql.SQL("INSERT INTO {} ({}) VALUES {} RETURNING id").format(
        sql.Identifier(table),
        sql.SQL(", ").join(map(sql.Identifier, columns)),
        sql.SQL(", ").join([values] * len(rows)),
    )
    params = [row[column] for row in rows for column in columns]
    return [row[0] for row in conn.execute(query, params)]


def insert_table(conn, many=False):
    table = choose("Таблица", TABLES)
    rows = [read_row(table) for _ in range(count("Сколько строк") if many else 1)]
    with conn.transaction():
        ids = insert_rows(conn, table, rows)
    log(f"Добавлены строки с id: {', '.join(map(str, ids))}.")


def insert_orders(conn):
    orders = []
    for _ in range(count("Сколько заказов")):
        order = read_row("orders")
        items = [read_row("order_items", skip=("order_id",))
                 for _ in range(count("Сколько позиций в заказе"))]
        orders.append((order, items))
    ids = []
    with conn.transaction():
        for order, items in orders:
            order_id = insert_rows(conn, "orders", [order])[0]
            ids.append(order_id)
            insert_rows(conn, "order_items", [dict(order_id=order_id, **item) for item in items])
    log(f"Добавлены заказы с позициями: {', '.join(map(str, ids))}.")


MENU = {
    "1": select_rows,
    "2": update_one,
    "3": update_many,
    "4": insert_table,
    "5": lambda conn: insert_table(conn, many=True),
    "6": insert_orders,
}


def run(conn):
    log("Подключение успешно.")
    while True:
        print("\n1 — просмотр\n2 — обновить одну запись\n3 — обновить несколько записей"
              "\n4 — добавить строку\n5 — добавить несколько строк\n6 — добавить заказы и позиции\n0 — выход")
        action = input("Действие: ").strip()
        if action == "0":
            return
        try:
            if action not in MENU:
                raise ValueError("Выберите номер из меню.")
            MENU[action](conn)
        except ValueError as exc:
            log(str(exc), exc)
        except psycopg.IntegrityError as exc:
            log("Запись не сохранена: проверьте связи, ограничения и дубликаты.", exc)
        except psycopg.OperationalError as exc:
            log("Связь с БД прервана. Запустите приложение снова.", exc)
            return 1
        except psycopg.Error as exc:
            log("Запрос не выполнен. Проверьте значения и права доступа.", exc)


def main():
    try:
        user = input("Логин: ")
        password = getpass.getpass("Пароль: ")
        try:
            conn = connect(user, password)
        except (psycopg.Error, ValueError, OSError, KeyError) as exc:
            log("Не удалось подключиться. Проверьте логин, пароль и состояние БД.", exc)
            return 1
        with conn:
            return run(conn)
    except (KeyboardInterrupt, EOFError):
        print("\nРабота завершена.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
