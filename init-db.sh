#!/usr/bin/env bash
set -Eeuo pipefail
PGPASSWORD="$POSTGRES_PASSWORD" psql -v ON_ERROR_STOP=1 -U postgres -d "$POSTGRES_DB" \
  -v app_user="$APP_DB_USER" -v app_password="$APP_DB_PASSWORD" <<'SQL'
CREATE ROLE :"app_user" LOGIN PASSWORD :'app_password';
REVOKE CONNECT, TEMP ON DATABASE seminar_db FROM PUBLIC;
GRANT CONNECT ON DATABASE seminar_db TO :"app_user";
SQL
