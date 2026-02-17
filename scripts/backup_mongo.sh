#!/bin/bash
# backup_mongo.sh — Backup diario de MongoDB con rotación de 7 días
# Uso: ./scripts/backup_mongo.sh
# Cron: 0 19 * * * cd /root/SIPUD && ./scripts/backup_mongo.sh >> /var/log/sipud_backup.log 2>&1

set -euo pipefail

# Configuración (se puede sobreescribir con variables de entorno)
MONGODB_HOST="${MONGODB_HOST:-localhost}"
MONGODB_PORT="${MONGODB_PORT:-27017}"
MONGODB_DB="${MONGODB_DB:-inventory_db}"
BACKUP_DIR="${BACKUP_DIR:-$(dirname "$0")/../backups}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"

# Crear directorio si no existe
mkdir -p "$BACKUP_DIR"

# Timestamp para el backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="backup_${TIMESTAMP}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

echo "=== SIPUD Backup MongoDB ==="
echo "Fecha: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Base de datos: ${MONGODB_DB}"
echo "Destino: ${BACKUP_PATH}"

# Ejecutar mongodump
if mongodump \
    --host "${MONGODB_HOST}" \
    --port "${MONGODB_PORT}" \
    --db "${MONGODB_DB}" \
    --out "${BACKUP_PATH}" \
    --quiet; then

    # Comprimir backup
    tar -czf "${BACKUP_PATH}.tar.gz" -C "${BACKUP_DIR}" "${BACKUP_NAME}"
    rm -rf "${BACKUP_PATH}"

    SIZE=$(du -sh "${BACKUP_PATH}.tar.gz" | cut -f1)
    echo "OK: Backup creado (${SIZE}): ${BACKUP_PATH}.tar.gz"
else
    echo "ERROR: mongodump falló"
    exit 1
fi

# Rotación: eliminar backups más antiguos que RETENTION_DAYS días
DELETED=0
find "${BACKUP_DIR}" -name "backup_*.tar.gz" -type f -mtime +${RETENTION_DAYS} | while read old_backup; do
    rm -f "$old_backup"
    echo "Rotación: eliminado $(basename "$old_backup")"
    DELETED=$((DELETED + 1))
done

# También limpiar directorios viejos sin comprimir (por si quedaron)
find "${BACKUP_DIR}" -maxdepth 1 -name "backup_*" -type d -mtime +${RETENTION_DAYS} -exec rm -rf {} \;

echo "=== Backup completado ==="
