#!/bin/bash
# deploy.sh — Deploy SIPUD al VPS (sipud.cloud)
# Uso desde local: ./scripts/deploy.sh
#
# Requisitos en VPS:
#   - Docker + Docker Compose instalados
#   - DNS apuntando sipud.cloud → 72.61.4.202
#   - Puerto 80 y 443 abiertos

set -euo pipefail

# === Configuración ===
VPS_USER="root"
VPS_HOST="72.61.4.202"
VPS_DIR="/root/SIPUD"
DOMAIN="sipud.cloud"

echo "=== SIPUD Deploy ==="
echo "Servidor: ${VPS_USER}@${VPS_HOST}"
echo "Directorio: ${VPS_DIR}"
echo ""

# === 1. Sync código al VPS ===
echo "[1/5] Sincronizando código al VPS..."
rsync -avz --delete \
    --exclude='.git' \
    --exclude='venv/' \
    --exclude='.venv/' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='backups/' \
    --exclude='___documentos/' \
    --exclude='.claude/' \
    --exclude='docs/' \
    --exclude='tests/' \
    --exclude='.DS_Store' \
    --exclude='*.log' \
    --exclude='node_modules/' \
    ./ ${VPS_USER}@${VPS_HOST}:${VPS_DIR}/

echo ""

# === 2. Verificar si SSL ya existe ===
echo "[2/5] Verificando SSL..."
SSL_EXISTS=$(ssh ${VPS_USER}@${VPS_HOST} "test -f /root/SIPUD/certbot_certs/_data/live/${DOMAIN}/fullchain.pem 2>/dev/null && echo 'yes' || echo 'no'")

if [ "$SSL_EXISTS" = "no" ]; then
    echo "  SSL no encontrado. Se usará config HTTP inicial para obtener certificado."
    echo "  Después del deploy, ejecuta: ./scripts/deploy.sh --ssl"
fi

echo ""

# === 3. Build y deploy ===
echo "[3/5] Construyendo y desplegando contenedores..."
ssh ${VPS_USER}@${VPS_HOST} << 'DEPLOY_CMDS'
cd /root/SIPUD

# Si no hay certificado SSL, usar config inicial (HTTP only)
if [ ! -f /var/lib/docker/volumes/sipud_certbot_certs/_data/live/sipud.cloud/fullchain.pem ] 2>/dev/null; then
    echo "  → Usando nginx-initial.conf (sin SSL)"
    cp nginx/nginx-initial.conf nginx/nginx.conf
fi

# Build y levantar
docker compose build --no-cache web
docker compose up -d

echo ""
echo "  Contenedores:"
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
DEPLOY_CMDS

echo ""

# === 4. Configurar backup cron ===
echo "[4/5] Configurando backup automático..."
ssh ${VPS_USER}@${VPS_HOST} << 'CRON_CMDS'
# Crear script de backup que ejecuta mongodump dentro del container
cat > /root/SIPUD/backup_cron.sh << 'SCRIPT'
#!/bin/bash
BACKUP_DIR="/root/SIPUD/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"

# Ejecutar mongodump dentro del container mongo
docker exec sipud_mongo mongodump \
    --db inventory_db \
    --out /tmp/backup_${TIMESTAMP} \
    --quiet 2>/dev/null

# Copiar backup del container al host
docker cp sipud_mongo:/tmp/backup_${TIMESTAMP} ${BACKUP_DIR}/backup_${TIMESTAMP}

# Comprimir
cd ${BACKUP_DIR}
tar -czf backup_${TIMESTAMP}.tar.gz backup_${TIMESTAMP}
rm -rf backup_${TIMESTAMP}

# Rotación: mantener últimos 7 días
find ${BACKUP_DIR} -name "backup_*.tar.gz" -mtime +7 -delete

# Limpiar tmp del container
docker exec sipud_mongo rm -rf /tmp/backup_${TIMESTAMP} 2>/dev/null

echo "$(date '+%Y-%m-%d %H:%M:%S') - Backup OK: backup_${TIMESTAMP}.tar.gz ($(du -sh ${BACKUP_DIR}/backup_${TIMESTAMP}.tar.gz | cut -f1))"
SCRIPT
chmod +x /root/SIPUD/backup_cron.sh

# Agregar al cron si no existe
CRON_JOB="0 19 * * * /root/SIPUD/backup_cron.sh >> /var/log/sipud_backup.log 2>&1"
(crontab -l 2>/dev/null | grep -v "sipud_backup" ; echo "$CRON_JOB") | crontab -
echo "  Cron configurado: backup diario a las 19:00"
CRON_CMDS

echo ""

# === 5. Verificar ===
echo "[5/5] Verificando deploy..."
sleep 5
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://${DOMAIN}/ --max-time 10 2>/dev/null || echo "000")
echo "  HTTP response: ${HTTP_CODE}"

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
    echo ""
    echo "=== Deploy exitoso ==="
    echo "  URL: http://${DOMAIN}"
    echo ""
    echo "  Próximos pasos:"
    echo "  1. Si no tienes SSL: ./scripts/deploy.sh --ssl"
    echo "  2. Verificar login en https://${DOMAIN}"
elif [ "$HTTP_CODE" = "301" ]; then
    echo ""
    echo "=== Deploy exitoso (con SSL) ==="
    echo "  URL: https://${DOMAIN}"
else
    echo ""
    echo "  ⚠ No se pudo verificar (código ${HTTP_CODE})"
    echo "  Revisa los logs: ssh ${VPS_USER}@${VPS_HOST} 'cd ${VPS_DIR} && docker compose logs --tail=50'"
fi
