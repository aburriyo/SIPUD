#!/bin/bash

# Script para crear imágenes placeholder para el manual de usuario SIPUD
# Requiere ImageMagick instalado: brew install imagemagick

IMGDIR="imagenes"
mkdir -p "$IMGDIR"

echo "Creando imágenes placeholder para el Manual de Usuario SIPUD..."

# Array de imágenes necesarias
declare -a images=(
    "logo_sipud.png:Logo SIPUD"
    "pantalla_login.png:Pantalla de Login"
    "dashboard_principal.png:Dashboard Principal"
    "catalogo_productos.png:Catálogo de Productos"
    "modulo_ventas.png:Módulo de Ventas"
    "buscador_productos_venta.png:Buscador de Productos"
    "modal_pagos.png:Modal de Pagos"
    "dashboard_bodega.png:Dashboard Bodega"
    "formulario_recepcion.png:Formulario de Recepción"
    "formulario_merma.png:Registro de Mermas"
    "gestion_vencimientos.png:Gestión de Vencimientos"
    "admin_usuarios.png:Panel de Usuarios"
    "activity_log.png:Registro de Actividades"
)

# Crear cada imagen
for item in "${images[@]}"; do
    filename="${item%%:*}"
    label="${item##*:}"
    
    echo "  - Creando $filename..."
    
    convert -size 1200x800 xc:white \
        -fill "#E5E7EB" -draw "rectangle 0,0 1200,800" \
        -fill "#2563EB" -draw "rectangle 20,20 1180,100" \
        -pointsize 48 -fill white -font "Helvetica-Bold" \
        -annotate +50+75 "SIPUD" \
        -pointsize 32 -fill "#1F2937" \
        -annotate +500+450 "$label" \
        -pointsize 16 -fill "#6B7280" \
        -annotate +450+500 "[Captura de pantalla pendiente]" \
        "$IMGDIR/$filename"
done

echo ""
echo "✓ Todas las imágenes placeholder han sido creadas en $IMGDIR/"
echo ""
echo "Para reemplazarlas con capturas reales:"
echo "1. Ejecute SIPUD: python ~/Proyectos/SIPUD/run.py"
echo "2. Tome capturas de pantalla de cada módulo"
echo "3. Guárdelas en $IMGDIR/ con los mismos nombres"
echo "4. Recompile el manual: pdflatex manual_usuario.tex"
