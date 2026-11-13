#!/bin/bash
# Arranque de la réplica: la primera vez copia la primaria con pg_basebackup
# (-R deja configurada la conexión de streaming) y luego arranca en modo hot standby.
set -e

if [ ! -s "$PGDATA/PG_VERSION" ]; then
  echo "Réplica vacía: copiando datos desde db-primary..."
  until pg_isready -h db-primary -U "$POSTGRES_USER"; do sleep 1; done
  rm -rf "${PGDATA:?}"/*
  PGPASSWORD="$REPLICATION_PASSWORD" pg_basebackup \
    -h db-primary -U "$REPLICATION_USER" -D "$PGDATA" \
    -R -X stream -S replica_slot -P
  chmod 700 "$PGDATA"
fi

exec postgres -c hot_standby=on
