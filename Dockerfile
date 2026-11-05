FROM postgres:18-bookworm

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends locales \
    && sed -i 's/^# *\(ru_RU.UTF-8 UTF-8\)/\1/' /etc/locale.gen \
    && grep -q '^ru_RU.UTF-8 UTF-8$' /etc/locale.gen \
    && locale-gen ru_RU.UTF-8 \
    && locale -a | grep -qi '^ru_RU\.utf8$' \
    && rm -rf /var/lib/apt/lists/*

ENV LANG=ru_RU.UTF-8 \
    LC_ALL=ru_RU.UTF-8

COPY docker/postgresql.conf /etc/postgresql/custom-postgresql.conf
COPY docker/01-create-role.sh /docker-entrypoint-initdb.d/01-create-role.sh

# Образ подхватывает этот файл в контексте своего entrypoint.
RUN chmod 0644 /docker-entrypoint-initdb.d/01-create-role.sh
