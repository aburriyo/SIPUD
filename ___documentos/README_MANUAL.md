# Manual de Usuario SIPUD

## Descripción

Este directorio contiene el **Manual de Usuario** completo del sistema SIPUD en formato LaTeX.

**Archivo principal:** `manual_usuario.tex`

## Contenido del Manual

El manual incluye 9 capítulos completos:

1. **Introducción al Sistema SIPUD** - Descripción general, características, módulos
2. **Acceso al Sistema** - Login, recuperación de contraseña, multi-tenancy
3. **Dashboard Principal** - Vista general, métricas, navegación
4. **Gestión de Productos** - Catálogo, bundles, edición, stock
5. **Módulo de Ventas** - Ventas con despacho/en local, pagos múltiples, estados
6. **Módulo de Bodega** - 4 submódulos (pedidos, recepción, mermas, vencimientos)
7. **Panel de Administración** - Usuarios, roles, permisos, activity log
8. **Reportes y Exportaciones** - Excel, análisis de datos
9. **FAQ y Troubleshooting** - Preguntas frecuentes y solución de problemas

## Requisitos para Compilar

### En macOS

```bash
# Instalar MacTeX (distribución completa - ~4 GB)
brew install --cask mactex

# O instalar BasicTeX (distribución mínima - ~100 MB)
brew install --cask basictex

# Luego instalar paquetes adicionales
sudo tlmgr update --self
sudo tlmgr install babel-spanish tocloft enumitem tcolorbox tikz
```

### En Linux (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install texlive-latex-extra texlive-lang-spanish texlive-fonts-recommended
```

### En Windows

1. Descargar e instalar [MiKTeX](https://miktex.org/download) o [TeX Live](https://www.tug.org/texlive/)
2. Los paquetes faltantes se instalarán automáticamente al compilar

## Compilar el Manual

Una vez instalado LaTeX:

```bash
cd ~/Proyectos/SIPUD/___documentos

# Compilar (ejecutar 2 veces para generar el índice correctamente)
pdflatex manual_usuario.tex
pdflatex manual_usuario.tex

# Se generará el archivo: manual_usuario.pdf
```

## Imágenes Placeholder

El manual hace referencia a imágenes que deben crearse como capturas de pantalla del sistema real.

**Imágenes necesarias:**

```
___documentos/imagenes/
├── logo_sipud.png              (Logo del sistema)
├── pantalla_login.png          (Pantalla de inicio de sesión)
├── dashboard_principal.png     (Dashboard con métricas)
├── catalogo_productos.png      (Tabla de productos)
├── modulo_ventas.png           (Listado de ventas)
├── buscador_productos_venta.png (Buscador en formulario de venta)
├── modal_pagos.png             (Modal de gestión de pagos)
├── dashboard_bodega.png        (Dashboard del módulo bodega)
├── formulario_recepcion.png    (Recepción de mercancía)
├── formulario_merma.png        (Registro de mermas)
├── gestion_vencimientos.png    (Tabla de vencimientos)
├── admin_usuarios.png          (Panel de usuarios)
└── activity_log.png            (Registro de actividades)
```

### Crear Imágenes Placeholder

Si necesita compilar el manual antes de tener las capturas reales:

```bash
# Crear imágenes placeholder de 800x600 con ImageMagick
cd ~/Proyectos/SIPUD/___documentos/imagenes

convert -size 800x600 xc:lightgray -pointsize 24 -fill black \
  -annotate +250+300 "Logo SIPUD" logo_sipud.png

convert -size 800x600 xc:lightgray -pointsize 24 -fill black \
  -annotate +200+300 "Pantalla de Login" pantalla_login.png

# Repetir para cada imagen...
```

O usar un script automatizado (ver `crear_placeholders.sh`)

## Compilación Online

Si no quiere instalar LaTeX localmente, puede usar servicios online:

- **Overleaf** (https://www.overleaf.com) - Editor LaTeX online colaborativo
- **Papeeria** (https://papeeria.com) - Otro editor online

Simplemente suba el archivo `.tex` y compile desde el navegador.

## Personalización

El manual está completamente personalizado para SIPUD con:

- Colores corporativos (azul, verde, naranja, rojo)
- Cajas de información, advertencia y éxito
- Diagramas y tablas profesionales
- Índice automático
- Formato profesional listo para impresión

### Modificar Colores

Los colores se definen al inicio del documento:

```latex
\definecolor{sipudblue}{RGB}{37, 99, 235}
\definecolor{sipudgray}{RGB}{107, 114, 128}
\definecolor{sipudlight}{RGB}{239, 246, 255}
\definecolor{sipudgreen}{RGB}{34, 197, 94}
\definecolor{sipudred}{RGB}{239, 68, 68}
\definecolor{sipudorange}{RGB}{249, 115, 22}
```

Puede modificar los valores RGB según su identidad corporativa.

## Estructura del Documento

- **Portada:** Logo generado con TikZ + título profesional
- **Índice:** Generado automáticamente
- **Capítulos:** 9 capítulos completos con subsecciones
- **Apéndices:** Atajos de teclado y glosario
- **Formato:** A4, 12pt, márgenes profesionales

## Resultado Final

El manual compilado tendrá aproximadamente **35-40 páginas** en formato PDF profesional, listo para:

- Impresión
- Distribución digital
- Capacitación de usuarios
- Documentación corporativa

## Notas Técnicas

- **Codificación:** UTF-8 (soporta caracteres especiales en español)
- **Idioma:** Español (usando babel)
- **Fuentes:** T1 encoding para mejor calidad
- **Enlaces:** Hyperref con colores corporativos
- **Compatibilidad:** LaTeX 2e estándar

## Contacto

Para preguntas sobre el manual o el sistema SIPUD:

**Email:** soporte@sipud.com  
**Proyecto:** ~/Proyectos/SIPUD
