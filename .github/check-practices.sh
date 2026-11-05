#!/usr/bin/env bash
set -euo pipefail

git clone -q -b main "$GITHUB_SERVER_URL/$GITHUB_REPOSITORY" "$RUNNER_TEMP/task1"
git clone -q -b task-2 "$GITHUB_SERVER_URL/$GITHUB_REPOSITORY" "$RUNNER_TEMP/task2"

(
  cd "$RUNNER_TEMP/task1"
  trap 'docker compose down -v' EXIT
  cp .env.example .env
  sed -i 's/REPLACE_WITH_RANDOM_ADMIN_PASSWORD/CiAdmin_1/;s/REPLACE_WITH_RANDOM_APP_PASSWORD/CiReader_1/' .env
  docker compose up -d --build --wait
  python -m pip install -q -r requirements.txt
  printf '%s\n' seminar_user CiReader_1 | python -m src.app | tee result.txt
  grep -q 'PostgreSQL 18' result.txt
  grep -q 'Подключение успешно' result.txt
  actual=$(docker compose exec -T db bash -c 'PGPASSWORD="$POSTGRES_PASSWORD" psql -U postgres -d seminar_db -Atc "SELECT datcollate FROM pg_database WHERE datname = current_database(); SHOW password_encryption;"')
  grep -iqx 'ru_RU.UTF-\?8' <<< "$actual"
  grep -qx 'scram-sha-256' <<< "$actual"
)

(
  cd "$RUNNER_TEMP/task2"
  trap 'docker compose down -v --remove-orphans' EXIT
  docker compose build
  docker compose run --name pinger-check --rm -T --no-deps -e POLL_SECONDS=2 pinger >success.txt 2>failure.txt &
  wait_for() {
    for n in {1..35}; do
      if grep -q "$1" "$2"; then return; fi
      sleep 1
    done
    cat success.txt failure.txt
    return 1
  }
  wait_for 'Не удалось подключиться' failure.txt
  docker compose up -d db
  wait_for 'Подключение успешно: PostgreSQL 18' success.txt
  docker compose run --rm -T --no-deps pinger cat /app/logs/pinger.log | grep -q 'Подключение успешно'
  cat failure.txt success.txt
  docker stop pinger-check
)

(
  trap 'docker compose down -v' EXIT
  docker compose build
  docker compose up -d --wait db
  {
    printf '%s\n' bookshop_user DemoBookshop3_local
    printf '%s\n' 1 books 0
    printf '%s\n' 1 books 1 author_id 1
    printf '%s\n' 1 books 2 author_id 1 price 450
    printf '%s\n' 2 books 1 2 title 'Проверка' price 999.90
    printf '%s\n' 3 books price 500 id 2 2 3
    printf '%s\n' 4 authors "O'Connor"
    printf '%s\n' 5 authors 2 'Автор 1' 'Автор 2'
    printf '%s\n' 6 1 1 new 2 1 2 3 1
    printf '%s\n' 6 2 1 new 1 1 1 2 paid 1 4 2
    printf '%s\n' 6 1 1 new 1 999 1
    printf '%s\n' 1 'books; DROP TABLE books' 0
  } | docker compose run --rm -T app >output.txt 2>error.txt
  cat output.txt error.txt
  grep -q 'Подключение успешно' output.txt
  grep -q 'Обновлено строк: 1' output.txt
  grep -q 'Обновлено строк: 2' output.txt
  grep -q 'Добавлены строки с id: 5, 6' output.txt
  grep -q 'Добавлены заказы с позициями: 4, 5' output.txt
  grep -q 'Запись не сохранена' error.txt
  grep -q 'Такого пункта или поля нет' error.txt
  test "$(grep -c 'Запрос выполнен' output.txt)" -eq 3
  actual=$(docker compose exec -T -e PGPASSWORD=DemoBookshop3_local db psql -U bookshop_user -d bookshop -Atc "SELECT count(*) FROM orders; SELECT count(*) FROM order_items; SELECT title FROM books WHERE id=1; SELECT count(*) FROM authors;")
  test "$actual" = $'5\n7\nПроверка\n6'
  if docker compose exec -T -e PGPASSWORD=DemoBookshop3_local db psql -U bookshop_user -d bookshop -v ON_ERROR_STOP=1 -c 'UPDATE books SET id = 10 WHERE id = 1'; then exit 1; fi
  if docker compose exec -T -e PGPASSWORD=DemoBookshop3_local db psql -U bookshop_user -d bookshop -v ON_ERROR_STOP=1 -c 'DELETE FROM books WHERE id = 4'; then exit 1; fi
  docker compose run --rm -T app cat /app/logs/bookshop.log | grep -q 'foreign key constraint'
)
