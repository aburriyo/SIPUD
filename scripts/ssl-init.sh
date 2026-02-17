#!/bin/bash
# ssl-init.sh — Obtener certificado SSL con Let's Encrypt para sipud.cloud
# Ejecutar en el VPS después del primer deploy
# Uso: ssh root@72.61.4.202 'cd /root/SIPUD && ./scripts/ssl-init.sh'

set -euo pipefail

DOMAIN="sipud.cloud"
EMAIL="admin@${DOMAIN}"

echo "=== Obtener SSL para ${DOMAIN} ==="

# 1. Asegurar que nginx está corriendo con config inicial (sin SSL)
echo "[1/4] Verificando nginx con config HTTP..."
cp nginx/nginx-initial.conf nginx/nginx.conf
docker compose up -d nginx
sleep 3

# 2. Obtener certificado
echo "[2/4] Solicitando certificado a Let's Encrypt..."
docker compose run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    -d ${DOMAIN} \
    --email ${EMAIL} \
    --agree-tos \
    --no-eff-email

# 3. Verificar que se creó el certificado
if docker compose run --rm certbot certificates | grep -q "${DOMAIN}"; then
    echo "[3/4] Certificado obtenido correctamente"
else
    echo "ERROR: No se pudo obtener el certificado"
    echo "Verifica que el DNS de ${DOMAIN} apunte a este servidor"
    exit 1
fi

# 4. Cambiar a config con SSL y reiniciar
echo "[4/4] Activando configuración HTTPS..."

# Restaurar nginx.conf con SSL
cat > nginx/nginx.conf << 'NGINX_SSL'
upstream sipud_app {
    server web:5006;
}

server {
    listen 80;
    server_name sipud.cloud www.sipud.cloud;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name sipud.cloud www.sipud.cloud;

    ssl_certificate /etc/letsencrypt/live/sipud.cloud/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/sipud.cloud/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    client_max_body_size 10M;

    location /static/ {
        alias /app/app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location / {
        proxy_pass http://sipud_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_connect_timeout 60s;
        proxy_read_timeout 120s;
        proxy_send_timeout 120s;
    }
}
NGINX_SSL

docker compose restart nginx

echo ""
echo "=== SSL configurado ==="
echo "  URL: https://${DOMAIN}"
echo "  Renovación automática: certbot container cada 12h"
