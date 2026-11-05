#!/usr/bin/env bash
set -Eeuo pipefail
PGPASSWORD="$POSTGRES_PASSWORD" psql -v ON_ERROR_STOP=1 -U postgres -d "$POSTGRES_DB" \
  -v app_password="$BOOKSHOP_PASSWORD" <<'SQL'
CREATE ROLE bookshop_user LOGIN PASSWORD :'app_password';
REVOKE CONNECT, TEMP ON DATABASE bookshop FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT CONNECT ON DATABASE bookshop TO bookshop_user;
GRANT USAGE ON SCHEMA public TO bookshop_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO bookshop_user;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO bookshop_user;
GRANT INSERT (name), UPDATE (name) ON authors TO bookshop_user;
GRANT INSERT (author_id, title, price), UPDATE (author_id, title, price) ON books TO bookshop_user;
GRANT INSERT (name, email), UPDATE (name, email) ON customers TO bookshop_user;
GRANT INSERT (customer_id, status), UPDATE (customer_id, status) ON orders TO bookshop_user;
GRANT INSERT (order_id, book_id, quantity), UPDATE (order_id, book_id, quantity) ON order_items TO bookshop_user;
SQL
