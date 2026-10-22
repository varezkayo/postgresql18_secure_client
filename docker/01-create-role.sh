#!/usr/bin/env bash
# Runs only once, during first initialization of an empty PostgreSQL volume.
set -Eeuo pipefail

: "${APP_DB_PASSWORD:?APP_DB_PASSWORD must be set}"

# Important: -v passes the password as a psql variable; :'app_password'
# safely quotes it as a SQL literal, without interpolating raw SQL.
# docker_process_sql is supplied by the official postgres entrypoint.
docker_process_sql --dbname "$POSTGRES_DB" -v app_password="$APP_DB_PASSWORD" <<'SQL'
CREATE ROLE seminar_user LOGIN PASSWORD :'app_password';
GRANT CONNECT ON DATABASE seminar_db TO seminar_user;
GRANT USAGE ON SCHEMA public TO seminar_user;
SQL
