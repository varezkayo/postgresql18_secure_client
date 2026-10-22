#!/usr/bin/env bash
set -Eeuo pipefail
export PGPASSWORD="${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}"

psql -X -v ON_ERROR_STOP=1 -U postgres -d seminar_db <<'SQL'
\echo '=== PostgreSQL version ==='
SELECT version();
\echo '=== Database locale and encoding ==='
SELECT datname, pg_encoding_to_char(encoding) AS encoding,
       datcollate AS lc_collate, datctype AS lc_ctype
FROM pg_database WHERE datname = 'seminar_db';
\echo '=== Default password encryption ==='
SHOW password_encryption;
\echo '=== Role credentials format (no password exposed) ==='
SELECT rolname, rolpassword LIKE 'SCRAM-SHA-256$%' AS stored_as_scram
FROM pg_authid WHERE rolname = 'seminar_user';
\echo '=== Role permissions ==='
SELECT has_database_privilege('seminar_user', 'seminar_db', 'CONNECT') AS database_connect,
       has_schema_privilege('seminar_user', 'public', 'USAGE') AS public_schema_usage;
\echo '=== HBA authentication rules ==='
SELECT type, database, user_name, address, auth_method
FROM pg_hba_file_rules
WHERE auth_method IS NOT NULL;
\echo '=== Assertions (any mismatch fails verification) ==='
DO $$
BEGIN
    IF current_setting('server_version_num')::integer / 10000 <> 18 THEN
        RAISE EXCEPTION 'Expected PostgreSQL major version 18';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_database
        WHERE datname = 'seminar_db'
          AND pg_encoding_to_char(encoding) = 'UTF8'
          AND lower(replace(datcollate, '-', '')) = 'ru_ru.utf8'
          AND lower(replace(datctype, '-', '')) = 'ru_ru.utf8'
    ) THEN
        RAISE EXCEPTION 'Expected seminar_db with UTF8 and ru_RU.UTF-8';
    END IF;
    IF current_setting('password_encryption') <> 'scram-sha-256' THEN
        RAISE EXCEPTION 'Expected password_encryption=scram-sha-256';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_authid WHERE rolname = 'seminar_user'
          AND rolcanlogin AND NOT rolsuper AND NOT rolcreatedb AND NOT rolcreaterole
          AND rolpassword LIKE 'SCRAM-SHA-256$%'
    ) THEN
        RAISE EXCEPTION 'Expected a non-privileged login with a SCRAM password';
    END IF;
    IF NOT has_database_privilege('seminar_user', 'seminar_db', 'CONNECT')
       OR NOT has_schema_privilege('seminar_user', 'public', 'USAGE') THEN
        RAISE EXCEPTION 'Missing database CONNECT or schema USAGE privilege';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_hba_file_rules WHERE error IS NOT NULL)
       OR NOT EXISTS (SELECT 1 FROM pg_hba_file_rules WHERE auth_method = 'scram-sha-256')
       OR EXISTS (
           SELECT 1 FROM pg_hba_file_rules
           WHERE auth_method IS NOT NULL AND auth_method <> 'scram-sha-256'
       ) THEN
        RAISE EXCEPTION 'Expected valid HBA rules using only SCRAM-SHA-256';
    END IF;
END
$$;
\echo 'PASS: PostgreSQL version, locale, SCRAM, HBA and role privileges'
SQL
