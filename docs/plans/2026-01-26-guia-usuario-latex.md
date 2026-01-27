# Guia de Usuario SIPUD - Documento LaTeX - Plan de Implementacion

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Crear un documento LaTeX profesional que sirva como guia de usuario completa del sistema SIPUD, con capturas de pantalla, diagramas y explicaciones paso a paso para cada modulo.

**Architecture:** Documento LaTeX modular usando el paquete `tcolorbox` para cajas informativas, `graphicx` para capturas de pantalla, `hyperref` para navegacion interna, y `fancyhdr` para encabezados profesionales. Se organizara en capitulos por modulo del sistema (Login, Dashboard, Productos, Ventas, Almacen, Admin, Reportes). Incluira un script Python para capturar pantallazos automaticamente usando Selenium/Playwright.

**Tech Stack:** LaTeX (pdflatex), Python (Selenium para capturas), paquetes LaTeX: tcolorbox, graphicx, hyperref, fancyhdr, geometry, babel, fontenc, inputenc, enumitem, tabularx, xcolor, listings

---

## Estructura del Documento Final

```
___documentos/
  guia_usuario/
    main.tex                    # Documento principal (incluye todos los capitulos)
    capitulos/
      01_introduccion.tex       # Que es SIPUD, requisitos, acceso
      02_login.tex              # Autenticacion y configuracion de cuenta
      03_dashboard.tex          # Panel principal y metricas
      04_productos.tex          # Gestion de productos y catalogo
      05_ventas.tex             # Creacion y gestion de ventas
      06_almacen.tex            # Operaciones de almacen (pedidos, recepcion, mermas, vencimientos)
      07_admin.tex              # Panel de administracion (usuarios, log de actividad)
      08_reportes.tex           # Exportaciones Excel
      09_roles.tex              # Permisos por rol
      10_faq.tex                # Preguntas frecuentes y solucion de problemas
    imagenes/                   # Capturas de pantalla (placeholder inicialmente)
      login.png
      dashboard_admin.png
      dashboard_warehouse.png
      productos_lista.png
      productos_crear.png
      ventas_lista.png
      ventas_crear.png
      almacen_dashboard.png
      almacen_pedidos.png
      almacen_recepcion.png
      almacen_mermas.png
      almacen_vencimientos.png
      admin_usuarios.png
      admin_actividad.png
      reportes_exportar.png
    estilos/
      sipud-style.sty           # Paquete de estilos personalizado
    scripts/
      capturar_pantallas.py     # Script para captura automatica de pantallazos
```

---

### Task 1: Crear estructura de directorios y paquete de estilos

**Files:**
- Create: `___documentos/guia_usuario/estilos/sipud-style.sty`

**Step 1: Crear directorios**

```bash
mkdir -p ___documentos/guia_usuario/{capitulos,imagenes,estilos,scripts}
```

**Step 2: Crear paquete de estilos `sipud-style.sty`**

```latex
\NeedsTeXFormat{LaTeX2e}
\ProvidesPackage{estilos/sipud-style}[2026/01/26 SIPUD User Guide Style]

% Paquetes base
\RequirePackage[utf8]{inputenc}
\RequirePackage[spanish]{babel}
\RequirePackage[T1]{fontenc}
\RequirePackage{lmodern}
\RequirePackage[margin=2.5cm]{geometry}
\RequirePackage{graphicx}
\RequirePackage{xcolor}
\RequirePackage{tcolorbox}
\RequirePackage{enumitem}
\RequirePackage{tabularx}
\RequirePackage{booktabs}
\RequirePackage{fancyhdr}
\RequirePackage{hyperref}
\RequirePackage{fontawesome5}
\RequirePackage{listings}
\RequirePackage{caption}
\RequirePackage{float}
\RequirePackage{titlesec}
\RequirePackage{tocloft}
\RequirePackage{pifont}

% Colores SIPUD
\definecolor{sipudOrange}{HTML}{C85103}
\definecolor{sipudDark}{HTML}{1F2937}
\definecolor{sipudGray}{HTML}{6B7280}
\definecolor{sipudLight}{HTML}{F3F4F6}
\definecolor{sipudGreen}{HTML}{059669}
\definecolor{sipudRed}{HTML}{DC2626}
\definecolor{sipudBlue}{HTML}{2563EB}
\definecolor{sipudYellow}{HTML}{D97706}

% Configuracion de hyperref
\hypersetup{
    colorlinks=true,
    linkcolor=sipudOrange,
    urlcolor=sipudBlue,
    citecolor=sipudGreen,
    pdftitle={SIPUD - Guia de Usuario},
    pdfauthor={Puerto Distribucion},
    pdfsubject={Manual de Usuario del Sistema SIPUD},
}

% Encabezados y pies de pagina
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small\textcolor{sipudGray}{SIPUD -- Guia de Usuario}}
\fancyhead[R]{\small\textcolor{sipudGray}{\leftmark}}
\fancyfoot[C]{\small\textcolor{sipudGray}{\thepage}}
\fancyfoot[R]{\small\textcolor{sipudGray}{v1.0 -- Enero 2026}}
\renewcommand{\headrulewidth}{0.4pt}
\renewcommand{\footrulewidth}{0.4pt}

% Formato de titulos
\titleformat{\section}
  {\normalfont\Large\bfseries\color{sipudOrange}}
  {\thesection}{1em}{}[\titlerule]

\titleformat{\subsection}
  {\normalfont\large\bfseries\color{sipudDark}}
  {\thesubsection}{1em}{}

\titleformat{\subsubsection}
  {\normalfont\normalsize\bfseries\color{sipudGray}}
  {\thesubsubsection}{1em}{}

% Cajas informativas con tcolorbox
\tcbuselibrary{skins, breakable}

\newtcolorbox{infobox}[1][]{
    enhanced, breakable,
    colback=sipudBlue!5,
    colframe=sipudBlue,
    coltitle=white,
    fonttitle=\bfseries,
    title={\faIcon{info-circle} ~Informacion},
    #1
}

\newtcolorbox{warningbox}[1][]{
    enhanced, breakable,
    colback=sipudYellow!5,
    colframe=sipudYellow,
    coltitle=white,
    fonttitle=\bfseries,
    title={\faIcon{exclamation-triangle} ~Advertencia},
    #1
}

\newtcolorbox{tipbox}[1][]{
    enhanced, breakable,
    colback=sipudGreen!5,
    colframe=sipudGreen,
    coltitle=white,
    fonttitle=\bfseries,
    title={\faIcon{lightbulb} ~Consejo},
    #1
}

\newtcolorbox{dangerbox}[1][]{
    enhanced, breakable,
    colback=sipudRed!5,
    colframe=sipudRed,
    coltitle=white,
    fonttitle=\bfseries,
    title={\faIcon{exclamation-circle} ~Importante},
    #1
}

\newtcolorbox{stepbox}[2][]{
    enhanced, breakable,
    colback=sipudLight,
    colframe=sipudOrange,
    coltitle=white,
    fonttitle=\bfseries,
    title={Paso #2},
    #1
}

% Comando para capturas de pantalla
\newcommand{\screenshot}[3][width=\textwidth]{%
    \begin{figure}[H]
        \centering
        \IfFileExists{imagenes/#2}{%
            \includegraphics[#1]{imagenes/#2}%
        }{%
            \fcolorbox{sipudGray}{sipudLight}{%
                \parbox{0.8\textwidth}{%
                    \centering\vspace{2cm}%
                    {\Large\color{sipudGray}\faIcon{image}}\\[0.5cm]%
                    {\color{sipudGray}Captura: \texttt{#2}}\\%
                    {\small\color{sipudGray}(Pendiente de agregar)}%
                    \vspace{2cm}%
                }%
            }%
        }
        \caption{#3}
        \label{fig:#2}
    \end{figure}
}

% Comando para pasos numerados con icono
\newcommand{\paso}[2]{%
    \noindent\textcolor{sipudOrange}{\textbf{#1.}} #2\par\vspace{0.3em}%
}

% Comando para atajos de teclado
\newcommand{\tecla}[1]{\texttt{\colorbox{sipudLight}{\textcolor{sipudDark}{#1}}}}

% Comando para elementos de menu
\newcommand{\menu}[1]{\textbf{\textcolor{sipudDark}{#1}}}

% Comando para botones
\newcommand{\boton}[1]{%
    \tcbox[on line, colback=sipudOrange!10, colframe=sipudOrange,
           size=small, arc=3pt, boxrule=0.5pt]{%
        \textcolor{sipudOrange}{\small\textbf{#1}}%
    }%
}

% Comando para roles
\newcommand{\rol}[1]{%
    \tcbox[on line, colback=sipudBlue!10, colframe=sipudBlue,
           size=small, arc=3pt, boxrule=0.5pt]{%
        \textcolor{sipudBlue}{\small\textbf{#1}}%
    }%
}

% Configuracion de listings para URLs
\lstset{
    basicstyle=\small\ttfamily,
    breaklines=true,
    frame=single,
    backgroundcolor=\color{sipudLight},
    rulecolor=\color{sipudGray},
}
```

**Step 3: Commit**

```bash
git add ___documentos/guia_usuario/
git commit -m "feat: create LaTeX user guide directory structure and style package"
```

---

### Task 2: Crear documento principal (main.tex)

**Files:**
- Create: `___documentos/guia_usuario/main.tex`

**Step 1: Crear `main.tex`**

```latex
%!TEX encoding = UTF-8 Unicode
\documentclass[12pt, a4paper]{article}

\usepackage{estilos/sipud-style}

\begin{document}

% --- PORTADA ---
\begin{titlepage}
    \centering
    \vspace*{2cm}

    {\Huge\bfseries\textcolor{sipudOrange}{SIPUD}\par}
    \vspace{0.5cm}
    {\Large\textcolor{sipudDark}{Sistema Integral de Gestion}\par}
    \vspace{0.3cm}
    {\large\textcolor{sipudGray}{Puerto Distribucion}\par}

    \vspace{2cm}

    \rule{\textwidth}{1.5pt}\\[0.5cm]
    {\LARGE\bfseries Guia de Usuario\par}
    \vspace{0.3cm}
    {\large Manual completo de operacion del sistema\par}
    \rule{\textwidth}{1.5pt}

    \vspace{2cm}

    \begin{tcolorbox}[colback=sipudLight, colframe=sipudOrange, width=0.8\textwidth]
        \centering
        \textbf{Version:} 1.0\\
        \textbf{Fecha:} Enero 2026\\
        \textbf{Sistema:} SIPUD v2.0 (MongoDB)\\
        \textbf{URL:} \url{http://localhost:5006}
    \end{tcolorbox}

    \vfill

    {\small\textcolor{sipudGray}{Documento confidencial -- Uso interno}\par}
\end{titlepage}

% --- TABLA DE CONTENIDOS ---
\newpage
\tableofcontents
\newpage

% --- CAPITULOS ---
\input{capitulos/01_introduccion}
\newpage
\input{capitulos/02_login}
\newpage
\input{capitulos/03_dashboard}
\newpage
\input{capitulos/04_productos}
\newpage
\input{capitulos/05_ventas}
\newpage
\input{capitulos/06_almacen}
\newpage
\input{capitulos/07_admin}
\newpage
\input{capitulos/08_reportes}
\newpage
\input{capitulos/09_roles}
\newpage
\input{capitulos/10_faq}

\end{document}
```

**Step 2: Commit**

```bash
git add ___documentos/guia_usuario/main.tex
git commit -m "feat: add main LaTeX document with title page and TOC"
```

---

### Task 3: Capitulo 1 - Introduccion

**Files:**
- Create: `___documentos/guia_usuario/capitulos/01_introduccion.tex`

**Step 1: Escribir capitulo de introduccion**

```latex
\section{Introduccion}
\label{sec:introduccion}

\subsection{Acerca de SIPUD}

SIPUD (\textbf{S}istema \textbf{I}ntegral de \textbf{P}uerto \textbf{U}nificado de \textbf{D}istribucion) es un sistema ERP disenado para gestionar de forma integral las operaciones de inventario, ventas, almacen y logistica de Puerto Distribucion.

El sistema permite:
\begin{itemize}[leftmargin=2em]
    \item \textbf{Gestion de Productos:} Catalogo completo con control de stock en tiempo real
    \item \textbf{Ventas:} Creacion, seguimiento y gestion de ventas con multiples metodos de pago
    \item \textbf{Almacen:} Pedidos a proveedores, recepcion de mercaderia, control de mermas y vencimientos
    \item \textbf{Administracion:} Gestion de usuarios, roles y permisos con registro de actividad
    \item \textbf{Reportes:} Exportacion de datos a Excel para analisis
\end{itemize}

\subsection{Requisitos del Sistema}

\begin{tabularx}{\textwidth}{lX}
    \toprule
    \textbf{Componente} & \textbf{Requisito} \\
    \midrule
    Navegador & Google Chrome (recomendado), Firefox, Edge -- version actualizada \\
    Conexion & Acceso a la red local o servidor donde se aloja SIPUD \\
    Resolucion & Minimo 1280x720 px (optimizado para 1920x1080) \\
    \bottomrule
\end{tabularx}

\subsection{Acceso al Sistema}

Para acceder a SIPUD, abra su navegador web e ingrese la siguiente direccion:

\begin{center}
    \Large\texttt{\textcolor{sipudBlue}{http://localhost:5006}}
\end{center}

\begin{infobox}
    Si accede desde otro equipo en la misma red, reemplace \texttt{localhost} por la direccion IP del servidor. Consulte con el administrador del sistema si no conoce esta direccion.
\end{infobox}

\subsection{Roles de Usuario}

SIPUD utiliza un sistema de roles para controlar el acceso a las diferentes funcionalidades. Existen cuatro roles principales:

\begin{enumerate}[leftmargin=2em]
    \item \rol{Administrador} -- Acceso completo a todos los modulos del sistema
    \item \rol{Gerente} -- Gestion de ventas, productos, almacen y monitoreo de actividad
    \item \rol{Almacen} -- Operaciones de bodega: pedidos, recepcion, mermas y vencimientos
    \item \rol{Ventas} -- Creacion y consulta de ventas, visualizacion de productos
\end{enumerate}

\begin{tipbox}
    Para conocer en detalle los permisos de cada rol, consulte la Seccion~\ref{sec:roles}.
\end{tipbox}

\subsection{Estructura de esta Guia}

Esta guia esta organizada por modulos del sistema. Cada capitulo incluye:
\begin{itemize}[leftmargin=2em]
    \item Descripcion general del modulo
    \item Capturas de pantalla con anotaciones
    \item Instrucciones paso a paso para cada operacion
    \item Consejos y advertencias importantes
    \item Permisos requeridos por rol
\end{itemize}
```

**Step 2: Commit**

```bash
git add ___documentos/guia_usuario/capitulos/01_introduccion.tex
git commit -m "feat: add introduction chapter for user guide"
```

---

### Task 4: Capitulo 2 - Login y Autenticacion

**Files:**
- Create: `___documentos/guia_usuario/capitulos/02_login.tex`

**Step 1: Escribir capitulo de login**

```latex
\section{Inicio de Sesion}
\label{sec:login}

\subsection{Pantalla de Inicio de Sesion}

Al acceder a SIPUD, se presentara la pantalla de inicio de sesion donde debera ingresar sus credenciales.

\screenshot{login.png}{Pantalla de inicio de sesion de SIPUD}

\subsubsection{Iniciar Sesion}

\begin{stepbox}{1}
    Ingrese su \textbf{nombre de usuario} en el campo correspondiente.
\end{stepbox}

\begin{stepbox}{2}
    Ingrese su \textbf{contrasena} en el campo de contrasena.
\end{stepbox}

\begin{stepbox}{3}
    (Opcional) Marque la casilla \boton{Recordarme} si desea mantener su sesion activa.
\end{stepbox}

\begin{stepbox}{4}
    Haga clic en el boton \boton{Iniciar Sesion} para acceder al sistema.
\end{stepbox}

\begin{warningbox}
    Despues de varios intentos fallidos de inicio de sesion, el sistema registrara la actividad sospechosa. Contacte al administrador si olvido sus credenciales.
\end{warningbox}

\subsection{Recuperar Contrasena}

Si olvido su contrasena, puede solicitar un restablecimiento:

\paso{1}{En la pantalla de login, haga clic en el enlace \menu{Olvide mi contrasena}}
\paso{2}{Ingrese el correo electronico asociado a su cuenta}
\paso{3}{Revise su bandeja de entrada y siga el enlace de restablecimiento}
\paso{4}{Ingrese y confirme su nueva contrasena}

\begin{infobox}
    El enlace de restablecimiento tiene una vigencia limitada. Si expira, solicite uno nuevo.
\end{infobox}

\subsection{Cambiar Contrasena}

Una vez dentro del sistema, puede cambiar su contrasena en cualquier momento:

\paso{1}{Haga clic en su nombre de usuario en la barra lateral}
\paso{2}{Seleccione \menu{Configuracion} o \menu{Cambiar Contrasena}}
\paso{3}{Ingrese su contrasena actual}
\paso{4}{Ingrese y confirme la nueva contrasena (minimo 4 caracteres)}
\paso{5}{Haga clic en \boton{Guardar Cambios}}

\subsection{Cerrar Sesion}

Para cerrar su sesion de forma segura:

\paso{1}{Haga clic en el boton \boton{Cerrar Sesion} ubicado en la parte inferior de la barra lateral}

\begin{dangerbox}
    Siempre cierre su sesion al terminar de usar el sistema, especialmente en equipos compartidos. El sistema registra todas las acciones asociadas a su cuenta.
\end{dangerbox}
```

**Step 2: Commit**

```bash
git add ___documentos/guia_usuario/capitulos/02_login.tex
git commit -m "feat: add login chapter for user guide"
```

---

### Task 5: Capitulo 3 - Dashboard

**Files:**
- Create: `___documentos/guia_usuario/capitulos/03_dashboard.tex`

**Step 1: Escribir capitulo del dashboard**

```latex
\section{Panel Principal (Dashboard)}
\label{sec:dashboard}

El dashboard es la primera pantalla que vera al iniciar sesion. Muestra un resumen de la actividad reciente y metricas clave del negocio. El contenido varia segun su rol de usuario.

\subsection{Dashboard del Administrador / Gerente}

\screenshot{dashboard_admin.png}{Dashboard principal -- vista de Administrador}

El dashboard de administrador incluye las siguientes secciones:

\subsubsection{Tarjeta de Bienvenida}
Muestra un saludo personalizado con su nombre, su rol actual y alertas criticas (productos con stock bajo o proximos a vencer).

\subsubsection{Accesos Rapidos}
Cuatro botones de acceso directo a las funciones mas utilizadas:
\begin{itemize}[leftmargin=2em]
    \item \boton{Nueva Venta} -- Crear una venta rapidamente
    \item \boton{Ver Productos} -- Acceder al catalogo de productos
    \item \boton{Pedidos Pendientes} -- Ver ordenes de compra sin recibir
    \item \boton{Reportes} -- Acceder a las exportaciones
\end{itemize}

\subsubsection{Metricas Principales}
\begin{tabularx}{\textwidth}{lX}
    \toprule
    \textbf{Metrica} & \textbf{Descripcion} \\
    \midrule
    Total Ventas & Numero total de ventas registradas \\
    Total Productos & Cantidad de productos en el catalogo \\
    Ingresos & Monto total de ventas (calculado desde los items) \\
    \bottomrule
\end{tabularx}

\subsubsection{Ultimas Ventas}
Tabla con las 5 ventas mas recientes, mostrando cliente, estado y monto.

\subsubsection{Productos Mas Vendidos}
Top 5 de productos con mayor cantidad vendida y sus ingresos asociados.

\subsubsection{Stock Critico}
Lista de productos cuyo stock actual esta por debajo o igual al nivel critico configurado.

\begin{warningbox}
    Los productos con stock critico requieren atencion inmediata. Coordine con el area de almacen para generar un pedido a proveedor.
\end{warningbox}

\subsubsection{Distribucion de Ventas por Estado}
Resumen visual de ventas agrupadas por estado de entrega: Pendiente, En Transito, Entregado, Cancelado, etc.

\subsubsection{Actividad Reciente}
Ultimas 5 acciones registradas en el sistema (creacion de ventas, modificaciones de productos, etc.).

\subsection{Dashboard de Almacen}

\screenshot{dashboard_warehouse.png}{Dashboard principal -- vista de Almacen}

El dashboard de almacen se enfoca en operaciones de bodega:

\begin{itemize}[leftmargin=2em]
    \item \textbf{Productos por Vencer:} Productos con fecha de vencimiento en los proximos 30 dias
    \item \textbf{Stock Critico:} Productos con niveles de stock por debajo del umbral
    \item \textbf{Pedidos Pendientes:} Ordenes de compra que aun no han sido recibidas
\end{itemize}

\subsection{Dashboard de Ventas}

El rol de ventas ve una version simplificada del dashboard con:
\begin{itemize}[leftmargin=2em]
    \item Metricas basicas de ventas
    \item Acceso rapido a crear nueva venta
    \item Productos disponibles para venta
\end{itemize}
```

**Step 2: Commit**

```bash
git add ___documentos/guia_usuario/capitulos/03_dashboard.tex
git commit -m "feat: add dashboard chapter for user guide"
```

---

### Task 6: Capitulo 4 - Productos

**Files:**
- Create: `___documentos/guia_usuario/capitulos/04_productos.tex`

**Step 1: Escribir capitulo de productos**

```latex
\section{Gestion de Productos}
\label{sec:productos}

El modulo de productos permite administrar el catalogo completo de articulos disponibles para venta. Desde aqui puede crear, editar, eliminar y consultar el stock de cada producto.

\begin{infobox}
    \textbf{Permisos requeridos:} \rol{Administrador}, \rol{Gerente} tienen acceso completo. \rol{Ventas} solo puede visualizar. \rol{Almacen} puede visualizar productos.
\end{infobox}

\subsection{Lista de Productos}

\screenshot{productos_lista.png}{Vista principal del catalogo de productos}

La vista principal muestra una tabla con todos los productos del tenant actual. Puede:
\begin{itemize}[leftmargin=2em]
    \item \textbf{Buscar:} Use el campo de busqueda para filtrar por nombre, SKU o categoria
    \item \textbf{Ordenar:} Haga clic en los encabezados de columna para ordenar
    \item \textbf{Paginar:} Navegue entre paginas si hay muchos productos
\end{itemize}

\subsubsection{Columnas de la Tabla}
\begin{tabularx}{\textwidth}{lX}
    \toprule
    \textbf{Columna} & \textbf{Descripcion} \\
    \midrule
    SKU & Codigo unico del producto (identificador interno) \\
    Nombre & Nombre descriptivo del producto \\
    Categoria & Clasificacion del producto (ej: Panaderia, Lacteos, Otros) \\
    Precio Base & Precio unitario de venta \\
    Stock & Cantidad total disponible (calculada desde los lotes) \\
    Stock Critico & Umbral minimo de alerta \\
    Estado & Indicador visual: verde (OK), rojo (critico), gris (sin stock) \\
    Acciones & Botones de editar y eliminar \\
    \bottomrule
\end{tabularx}

\subsection{Crear un Producto Nuevo}

\screenshot{productos_crear.png}{Formulario de creacion de producto}

Para agregar un nuevo producto al catalogo:

\begin{stepbox}{1}
    Haga clic en el boton \boton{Nuevo Producto} en la parte superior de la lista.
\end{stepbox}

\begin{stepbox}{2}
    Complete los campos del formulario:
    \begin{itemize}
        \item \textbf{Nombre} (obligatorio): Nombre descriptivo del producto
        \item \textbf{SKU} (obligatorio): Codigo unico. No puede repetirse dentro del mismo tenant
        \item \textbf{Descripcion}: Detalle adicional del producto
        \item \textbf{Categoria}: Seleccione o escriba una categoria (por defecto: ``Otros'')
        \item \textbf{Precio Base}: Precio unitario de venta
        \item \textbf{Stock Critico}: Cantidad minima antes de generar alerta
    \end{itemize}
\end{stepbox}

\begin{stepbox}{3}
    Haga clic en \boton{Guardar} para crear el producto.
\end{stepbox}

\begin{tipbox}
    El stock de un producto no se ingresa directamente. El stock se calcula automaticamente a partir de los \textbf{lotes} recibidos en el modulo de Almacen (ver Seccion~\ref{sec:almacen}).
\end{tipbox}

\subsection{Editar un Producto}

\paso{1}{En la lista de productos, haga clic en el icono de \textbf{editar} (lapiz) del producto deseado}
\paso{2}{Modifique los campos necesarios en el formulario}
\paso{3}{Haga clic en \boton{Guardar Cambios}}

\begin{warningbox}
    Cambiar el SKU de un producto puede afectar la trazabilidad de ventas e inventario historico. Realice este cambio con precaucion.
\end{warningbox}

\subsection{Eliminar un Producto}

\paso{1}{En la lista de productos, haga clic en el icono de \textbf{eliminar} (papelera) del producto}
\paso{2}{Confirme la eliminacion en el dialogo de confirmacion}

\begin{dangerbox}
    Al eliminar un producto se eliminan tambien todos sus lotes asociados y relaciones de bundles. Esta accion \textbf{no se puede deshacer}. Si el producto tiene ventas asociadas, considere desactivarlo en lugar de eliminarlo.
\end{dangerbox}

\subsection{Productos Kit / Bundle}

Un producto tipo \textbf{bundle} es un kit compuesto por otros productos. Por ejemplo, una ``Canasta Familiar'' puede estar compuesta por Pan, Leche y Huevos.

\begin{infobox}
    Los bundles se arman desde el modulo de Almacen (Seccion~\ref{subsec:assembly}). Al crear un bundle, el sistema descuenta el stock de los componentes y crea un lote para el producto armado.
\end{infobox}
```

**Step 2: Commit**

```bash
git add ___documentos/guia_usuario/capitulos/04_productos.tex
git commit -m "feat: add products chapter for user guide"
```

---

### Task 7: Capitulo 5 - Ventas

**Files:**
- Create: `___documentos/guia_usuario/capitulos/05_ventas.tex`

**Step 1: Escribir capitulo de ventas**

```latex
\section{Gestion de Ventas}
\label{sec:ventas}

El modulo de ventas permite crear, consultar y administrar las ventas realizadas a clientes. El sistema gestiona automaticamente el stock utilizando el metodo FIFO (primero en entrar, primero en salir).

\begin{infobox}
    \textbf{Permisos requeridos:} \rol{Administrador} y \rol{Gerente} tienen acceso completo. \rol{Ventas} puede crear y ver ventas. \rol{Almacen} no tiene acceso a este modulo.
\end{infobox}

\subsection{Lista de Ventas}

\screenshot{ventas_lista.png}{Vista principal del modulo de ventas}

La tabla de ventas muestra todas las ventas registradas con la siguiente informacion:

\begin{tabularx}{\textwidth}{lX}
    \toprule
    \textbf{Columna} & \textbf{Descripcion} \\
    \midrule
    ID & Identificador unico de la venta \\
    Cliente & Nombre del cliente \\
    Tipo de Venta & ``En Local'' (retiro en tienda) o ``Con Despacho'' (envio a domicilio) \\
    Estado Entrega & Pendiente, En Preparacion, En Transito, Entregado, Con Observaciones, Cancelado \\
    Estado Pago & Pagado, Pago Parcial, Deuda \\
    Total & Monto total de la venta \\
    Fecha & Fecha y hora de creacion \\
    \bottomrule
\end{tabularx}

\subsubsection{Codigos de Color -- Estado de Entrega}
\begin{itemize}[leftmargin=2em]
    \item \textcolor{sipudGray}{\ding{108}} \textbf{Pendiente:} Venta creada, sin preparar
    \item \textcolor{sipudBlue}{\ding{108}} \textbf{En Preparacion:} Se esta armando el pedido
    \item \textcolor{sipudYellow}{\ding{108}} \textbf{En Transito:} Pedido en camino al cliente
    \item \textcolor{sipudGreen}{\ding{108}} \textbf{Entregado:} Pedido entregado exitosamente
    \item \textcolor{orange}{\ding{108}} \textbf{Con Observaciones:} Entrega con novedades
    \item \textcolor{sipudRed}{\ding{108}} \textbf{Cancelado:} Venta cancelada
\end{itemize}

\subsubsection{Codigos de Color -- Estado de Pago}
\begin{itemize}[leftmargin=2em]
    \item \textcolor{sipudGreen}{\ding{108}} \textbf{Pagado:} Pago completo recibido
    \item \textcolor{sipudYellow}{\ding{108}} \textbf{Pago Parcial:} Se ha recibido un abono
    \item \textcolor{sipudRed}{\ding{108}} \textbf{Deuda:} Pago pendiente
\end{itemize}

\subsection{Crear una Nueva Venta}

\screenshot{ventas_crear.png}{Modal de creacion de venta}

Para registrar una nueva venta:

\begin{stepbox}{1}
    Haga clic en el boton \boton{Nueva Venta} en la parte superior.
\end{stepbox}

\begin{stepbox}{2}
    Ingrese el \textbf{nombre del cliente}.
\end{stepbox}

\begin{stepbox}{3}
    Seleccione el \textbf{tipo de venta}:
    \begin{itemize}
        \item \textbf{En Local:} El cliente retira en tienda
        \item \textbf{Con Despacho:} Se enviara al domicilio del cliente
    \end{itemize}
\end{stepbox}

\begin{stepbox}{4}
    \textbf{Agregar productos:}
    \begin{enumerate}
        \item Seleccione un producto del menu desplegable
        \item El sistema mostrara el stock disponible y el precio unitario
        \item Ingrese la cantidad deseada
        \item Haga clic en \boton{Agregar} para anadir el producto a la venta
        \item Repita para cada producto adicional
    \end{enumerate}
\end{stepbox}

\begin{stepbox}{5}
    Verifique el \textbf{resumen} de la venta: lista de productos, cantidades y total.
\end{stepbox}

\begin{stepbox}{6}
    Seleccione el \textbf{metodo de pago} y haga clic en \boton{Crear Venta}.
\end{stepbox}

\begin{warningbox}
    El sistema valida que haya stock suficiente de cada producto. Si el stock es insuficiente, la venta sera rechazada con un mensaje indicando la cantidad disponible.
\end{warningbox}

\begin{tipbox}
    \textbf{Sistema FIFO:} Al crear una venta, el sistema automaticamente descuenta el stock de los lotes mas antiguos primero. Esto garantiza la rotacion correcta del inventario.
\end{tipbox}

\subsection{Modificar una Venta}

Puede actualizar el estado de entrega y de pago de una venta existente:

\paso{1}{Haga clic en la venta que desea modificar}
\paso{2}{Cambie el estado de entrega o pago segun corresponda}
\paso{3}{Guarde los cambios}

\subsection{Cancelar una Venta}

\paso{1}{Abra la venta que desea cancelar}
\paso{2}{Cambie el estado a ``Cancelado''}
\paso{3}{Confirme la cancelacion}

\begin{dangerbox}
    Cancelar una venta \textbf{no revierte automaticamente} el stock descontado. Si necesita reponer el stock, debera registrar una nueva recepcion en el modulo de Almacen.
\end{dangerbox}
```

**Step 2: Commit**

```bash
git add ___documentos/guia_usuario/capitulos/05_ventas.tex
git commit -m "feat: add sales chapter for user guide"
```

---

### Task 8: Capitulo 6 - Almacen

**Files:**
- Create: `___documentos/guia_usuario/capitulos/06_almacen.tex`

**Step 1: Escribir capitulo de almacen**

```latex
\section{Operaciones de Almacen}
\label{sec:almacen}

El modulo de almacen concentra todas las operaciones de bodega: gestion de pedidos a proveedores, recepcion de mercaderia, registro de mermas y control de vencimientos.

\begin{infobox}
    \textbf{Permisos requeridos:} \rol{Almacen} tiene acceso principal. \rol{Administrador} y \rol{Gerente} tambien pueden acceder a todas las funciones.
\end{infobox}

\subsection{Dashboard de Almacen}

\screenshot{almacen_dashboard.png}{Panel principal del modulo de almacen}

El dashboard de almacen muestra tres secciones de alerta:

\begin{enumerate}[leftmargin=2em]
    \item \textbf{Productos por Vencer:} Los 10 productos con fecha de vencimiento mas proxima (dentro de los proximos 30 dias)
    \item \textbf{Stock Critico:} Los 10 productos con menor nivel de stock relativo a su umbral critico
    \item \textbf{Pedidos Pendientes:} Los 10 pedidos a proveedores que aun no han sido recibidos
\end{enumerate}

\subsection{Pedidos a Proveedores}
\label{subsec:pedidos}

\screenshot{almacen_pedidos.png}{Gestion de pedidos a proveedores}

Los pedidos representan ordenes de compra a proveedores. Permiten llevar un registro de lo que se ha solicitado y su estado de recepcion.

\subsubsection{Crear un Pedido}

\begin{stepbox}{1}
    Haga clic en \boton{Nuevo Pedido} en la vista de pedidos.
\end{stepbox}

\begin{stepbox}{2}
    Complete la informacion del pedido:
    \begin{itemize}
        \item \textbf{Proveedor}: Nombre del proveedor
        \item \textbf{Numero de Factura}: Numero o codigo de la factura del proveedor
        \item \textbf{Total}: Monto total del pedido
        \item \textbf{Notas}: Observaciones adicionales (opcional)
    \end{itemize}
\end{stepbox}

\begin{stepbox}{3}
    Haga clic en \boton{Guardar} para registrar el pedido.
\end{stepbox}

\subsubsection{Estados del Pedido}
\begin{tabularx}{\textwidth}{lX}
    \toprule
    \textbf{Estado} & \textbf{Descripcion} \\
    \midrule
    Pendiente & Pedido creado, mercaderia aun no recibida \\
    Recibido & Mercaderia recibida y lotes creados \\
    Pagado & Pedido pagado al proveedor \\
    \bottomrule
\end{tabularx}

\subsection{Recepcion de Mercaderia}
\label{subsec:recepcion}

\screenshot{almacen_recepcion.png}{Pantalla de recepcion de mercaderia}

La recepcion es el proceso donde se confirma la llegada de productos y se crean los \textbf{lotes} que alimentan el stock del sistema.

\begin{dangerbox}
    Este es el \textbf{unico proceso} que agrega stock al sistema. Sin recepcion, los productos tendran stock en cero y no podran venderse.
\end{dangerbox}

\subsubsection{Proceso de Recepcion}

\begin{stepbox}{1}
    En la vista de recepcion, localice el pedido pendiente que desea recibir.
\end{stepbox}

\begin{stepbox}{2}
    Haga clic en \boton{Confirmar Recepcion}. Se abrira un formulario para registrar los productos recibidos.
\end{stepbox}

\begin{stepbox}{3}
    Para cada producto recibido:
    \begin{enumerate}
        \item \textbf{Seleccione el producto} del catalogo
        \item Ingrese la \textbf{cantidad recibida}
        \item (Opcional) Ingrese un \textbf{codigo de lote} personalizado. Si no lo ingresa, se generara automaticamente
        \item (Opcional) Ingrese la \textbf{fecha de vencimiento} del lote
    \end{enumerate}
\end{stepbox}

\begin{stepbox}{4}
    Haga clic en \boton{Confirmar Recepcion} para finalizar.
\end{stepbox}

\begin{infobox}
    Al confirmar la recepcion:
    \begin{itemize}
        \item Se crean los lotes con la cantidad recibida
        \item El stock del producto se actualiza automaticamente
        \item El estado del pedido cambia a ``Recibido''
        \item Se registra la fecha de recepcion
        \item La accion queda registrada en el log de actividad
    \end{itemize}
\end{infobox}

\begin{tipbox}
    \textbf{Concepto de Lote:} Un lote es una unidad de inventario con cantidad y fecha de ingreso. El sistema FIFO siempre consume los lotes mas antiguos primero, garantizando la rotacion adecuada de productos.
\end{tipbox}

\subsection{Registro de Mermas}
\label{subsec:mermas}

\screenshot{almacen_mermas.png}{Formulario de registro de mermas}

Las mermas son perdidas de inventario por diversas causas. Registrar mermas descuenta stock del sistema usando el mismo metodo FIFO.

\subsubsection{Registrar una Merma}

\begin{stepbox}{1}
    En el modulo de mermas, seleccione el \textbf{producto} afectado.
\end{stepbox}

\begin{stepbox}{2}
    Ingrese la \textbf{cantidad} de unidades perdidas.
\end{stepbox}

\begin{stepbox}{3}
    Seleccione el \textbf{motivo} de la merma:
    \begin{itemize}
        \item \textbf{Vencido:} Producto que supero su fecha de vencimiento
        \item \textbf{Danado:} Producto danado fisicamente
        \item \textbf{Perdido:} Producto extraviado
        \item \textbf{Robo:} Producto hurtado
        \item \textbf{Otro:} Otra causa (especificar en notas)
    \end{itemize}
\end{stepbox}

\begin{stepbox}{4}
    (Opcional) Agregue \textbf{notas} con detalles adicionales.
\end{stepbox}

\begin{stepbox}{5}
    Haga clic en \boton{Registrar Merma} para confirmar.
\end{stepbox}

\begin{warningbox}
    El registro de mermas descuenta stock de forma permanente. Verifique bien la cantidad antes de confirmar. Solo usuarios con permiso pueden eliminar registros de merma (y esto \textbf{no} revierte el stock).
\end{warningbox}

\subsection{Control de Vencimientos}
\label{subsec:vencimientos}

\screenshot{almacen_vencimientos.png}{Control de fechas de vencimiento}

Este modulo permite monitorear y gestionar las fechas de vencimiento de los productos.

\subsubsection{Indicadores de Vencimiento}
\begin{itemize}[leftmargin=2em]
    \item \textcolor{sipudRed}{\ding{108}} \textbf{Rojo:} Producto vencido o vence en menos de 7 dias
    \item \textcolor{orange}{\ding{108}} \textbf{Naranja:} Producto vence en los proximos 14 dias
    \item \textcolor{sipudYellow}{\ding{108}} \textbf{Amarillo:} Producto vence en los proximos 30 dias
    \item \textcolor{sipudGreen}{\ding{108}} \textbf{Verde:} Producto con vencimiento superior a 30 dias
\end{itemize}

\subsubsection{Actualizar Fecha de Vencimiento}

\paso{1}{Localice el producto en la lista de vencimientos}
\paso{2}{Haga clic en el campo de fecha de vencimiento}
\paso{3}{Ingrese la nueva fecha de vencimiento}
\paso{4}{Confirme el cambio}

\begin{infobox}
    El sistema no permite ingresar fechas de vencimiento que ya hayan pasado.
\end{infobox}

\subsection{Armado de Bundles / Kits}
\label{subsec:assembly}

El armado de kits permite crear productos compuestos a partir de productos individuales.

\subsubsection{Proceso de Armado}

\begin{stepbox}{1}
    Seleccione el \textbf{producto bundle} a armar (debe tener componentes definidos previamente).
\end{stepbox}

\begin{stepbox}{2}
    Ingrese la \textbf{cantidad} de kits a armar.
\end{stepbox}

\begin{stepbox}{3}
    El sistema \textbf{verifica} que haya suficiente stock de todos los componentes.
\end{stepbox}

\begin{stepbox}{4}
    Confirme el armado. El sistema:
    \begin{itemize}
        \item Descuenta el stock de cada componente (FIFO)
        \item Crea un pedido interno (proveedor: ``Interno: Armado'')
        \item Crea un lote nuevo para el producto bundle
        \item Registra la operacion en el log de actividad
    \end{itemize}
\end{stepbox}

\begin{tipbox}
    Antes de armar kits, asegurese de que todos los productos componentes tengan stock suficiente. El sistema rechazara el armado si falta alguno.
\end{tipbox}
```

**Step 2: Commit**

```bash
git add ___documentos/guia_usuario/capitulos/06_almacen.tex
git commit -m "feat: add warehouse chapter for user guide"
```

---

### Task 9: Capitulo 7 - Administracion

**Files:**
- Create: `___documentos/guia_usuario/capitulos/07_admin.tex`

**Step 1: Escribir capitulo de administracion**

```latex
\section{Panel de Administracion}
\label{sec:admin}

El panel de administracion permite gestionar usuarios, asignar roles y monitorear la actividad del sistema.

\begin{dangerbox}
    \textbf{Acceso restringido:} Solo los usuarios con rol \rol{Administrador} tienen acceso completo al panel de administracion. Los \rol{Gerente} tienen acceso limitado (no pueden eliminar usuarios ni ver el log de actividad completo).
\end{dangerbox}

\subsection{Gestion de Usuarios}

\screenshot{admin_usuarios.png}{Panel de gestion de usuarios}

\subsubsection{Lista de Usuarios}

La tabla muestra todos los usuarios del tenant actual con:
\begin{tabularx}{\textwidth}{lX}
    \toprule
    \textbf{Columna} & \textbf{Descripcion} \\
    \midrule
    ID & Identificador unico del usuario \\
    Usuario & Nombre de usuario para login \\
    Email & Correo electronico (opcional) \\
    Nombre Completo & Nombre y apellido del usuario \\
    Rol & Rol asignado (admin, manager, warehouse, sales) \\
    Estado & Activo o Inactivo \\
    Ultimo Acceso & Fecha y hora del ultimo inicio de sesion \\
    Creado & Fecha de creacion del usuario \\
    \bottomrule
\end{tabularx}

\subsubsection{Crear un Usuario}

\begin{stepbox}{1}
    Haga clic en \boton{Nuevo Usuario}.
\end{stepbox}

\begin{stepbox}{2}
    Complete los campos:
    \begin{itemize}
        \item \textbf{Nombre de Usuario} (obligatorio): Minimo 3 caracteres, debe ser unico
        \item \textbf{Contrasena} (obligatorio): Minimo 4 caracteres
        \item \textbf{Email}: Correo electronico (opcional, pero debe ser unico si se ingresa)
        \item \textbf{Nombre Completo}: Nombre y apellido del usuario
        \item \textbf{Rol}: Seleccione el rol apropiado
    \end{itemize}
\end{stepbox}

\begin{stepbox}{3}
    Haga clic en \boton{Crear Usuario} para guardar.
\end{stepbox}

\begin{tipbox}
    Al asignar roles, considere el principio de \textbf{minimo privilegio}: otorgue solo los permisos necesarios para las funciones que realizara el usuario.
\end{tipbox}

\subsubsection{Editar un Usuario}

\paso{1}{Haga clic en el icono de edicion del usuario}
\paso{2}{Modifique los campos necesarios (email, nombre, rol, contrasena)}
\paso{3}{Guarde los cambios}

\begin{warningbox}
    No puede cambiar su propio rol. Si necesita modificar los permisos de un administrador, otro administrador debe realizar el cambio.
\end{warningbox}

\subsubsection{Desactivar / Reactivar un Usuario}

En lugar de eliminar usuarios, SIPUD utiliza \textbf{desactivacion}:

\paso{1}{Haga clic en el boton de eliminar/desactivar del usuario}
\paso{2}{Confirme la desactivacion}

El usuario desactivado no podra iniciar sesion pero su historial se conserva. Para reactivarlo:

\paso{1}{Localice el usuario inactivo en la lista}
\paso{2}{Haga clic en \boton{Reactivar}}

\begin{infobox}
    No puede desactivar su propia cuenta. Esto previene que el sistema quede sin administradores activos.
\end{infobox}

\subsection{Log de Actividad}

\screenshot{admin_actividad.png}{Monitor de actividad del sistema}

El log de actividad registra \textbf{todas} las acciones realizadas en el sistema, proporcionando una auditoria completa.

\subsubsection{Informacion Registrada}

Cada entrada del log incluye:
\begin{itemize}[leftmargin=2em]
    \item \textbf{Usuario:} Quien realizo la accion
    \item \textbf{Accion:} Tipo de operacion (crear, editar, eliminar, login, logout)
    \item \textbf{Modulo:} Area del sistema afectada (productos, ventas, usuarios, etc.)
    \item \textbf{Descripcion:} Detalle de lo que se hizo
    \item \textbf{Objetivo:} Entidad afectada
    \item \textbf{Direccion IP:} IP desde donde se realizo la accion
    \item \textbf{Fecha y Hora:} Momento exacto del evento
\end{itemize}

\subsubsection{Filtros Disponibles}

Puede filtrar el log por:
\begin{itemize}[leftmargin=2em]
    \item \textbf{Usuario:} Ver acciones de un usuario especifico
    \item \textbf{Accion:} Filtrar por tipo (crear, editar, eliminar, login)
    \item \textbf{Modulo:} Filtrar por area (productos, ventas, almacen, usuarios)
    \item \textbf{Rango de Fechas:} Ver actividad entre dos fechas especificas
\end{itemize}

\begin{tipbox}
    Use el log de actividad para auditar cambios importantes, investigar discrepancias de inventario o monitorear el uso del sistema.
\end{tipbox}
```

**Step 2: Commit**

```bash
git add ___documentos/guia_usuario/capitulos/07_admin.tex
git commit -m "feat: add admin panel chapter for user guide"
```

---

### Task 10: Capitulo 8 - Reportes

**Files:**
- Create: `___documentos/guia_usuario/capitulos/08_reportes.tex`

**Step 1: Escribir capitulo de reportes**

```latex
\section{Reportes y Exportaciones}
\label{sec:reportes}

SIPUD permite exportar datos a formato Excel (.xlsx) para analisis externo, contabilidad o respaldo.

\begin{infobox}
    \textbf{Permisos requeridos:} Se requiere el permiso \texttt{reports:export}. Los roles \rol{Administrador} y \rol{Gerente} tienen este permiso por defecto.
\end{infobox}

\screenshot{reportes_exportar.png}{Opciones de exportacion de reportes}

\subsection{Reportes Disponibles}

\subsubsection{Reporte de Ventas}

\begin{tabularx}{\textwidth}{lX}
    \toprule
    \textbf{Campo} & \textbf{Detalle} \\
    \midrule
    Acceso & Boton de exportacion en la vista de Ventas \\
    Formato & Excel (.xlsx) con encabezados azules \\
    Contenido & ID, Fecha, Cliente, Estado, Items, Total, Metodo de Pago \\
    Filtro & Exporta todas las ventas del tenant actual \\
    \bottomrule
\end{tabularx}

\subsubsection{Reporte de Inventario}

\begin{tabularx}{\textwidth}{lX}
    \toprule
    \textbf{Campo} & \textbf{Detalle} \\
    \midrule
    Acceso & Boton de exportacion en Productos o Dashboard \\
    Formato & Excel (.xlsx) con encabezados verdes \\
    Contenido & SKU, Nombre, Categoria, Precio Base, Stock Total, Stock Critico, Estado, Vencimiento \\
    Destacado & Filas con stock critico resaltadas en rojo claro \\
    \bottomrule
\end{tabularx}

\subsubsection{Reporte de Mermas}

\begin{tabularx}{\textwidth}{lX}
    \toprule
    \textbf{Campo} & \textbf{Detalle} \\
    \midrule
    Acceso & Boton de exportacion en la vista de Mermas \\
    Formato & Excel (.xlsx) con encabezados rojos \\
    Contenido & ID, Fecha, Producto, SKU, Cantidad, Motivo, Notas \\
    \bottomrule
\end{tabularx}

\subsubsection{Reporte de Pedidos}

\begin{tabularx}{\textwidth}{lX}
    \toprule
    \textbf{Campo} & \textbf{Detalle} \\
    \midrule
    Acceso & Boton de exportacion en la vista de Pedidos \\
    Formato & Excel (.xlsx) con encabezados azules \\
    Contenido & ID, Proveedor, N. Factura, Estado, Total, Fecha Creacion, Fecha Recepcion, Notas \\
    \bottomrule
\end{tabularx}

\subsection{Como Exportar un Reporte}

\begin{stepbox}{1}
    Navegue al modulo del cual desea exportar datos (Ventas, Productos, Mermas o Pedidos).
\end{stepbox}

\begin{stepbox}{2}
    Haga clic en el boton \boton{Exportar Excel} o el icono de descarga.
\end{stepbox}

\begin{stepbox}{3}
    El archivo se descargara automaticamente a su carpeta de descargas.
\end{stepbox}

\begin{tipbox}
    Los archivos exportados incluyen \textbf{todos} los registros del tenant actual, sin paginacion. Para grandes volumenes de datos, la generacion puede tomar unos segundos.
\end{tipbox}
```

**Step 2: Commit**

```bash
git add ___documentos/guia_usuario/capitulos/08_reportes.tex
git commit -m "feat: add reports chapter for user guide"
```

---

### Task 11: Capitulo 9 - Roles y Permisos

**Files:**
- Create: `___documentos/guia_usuario/capitulos/09_roles.tex`

**Step 1: Escribir capitulo de roles**

```latex
\section{Roles y Permisos}
\label{sec:roles}

SIPUD implementa un sistema de control de acceso basado en roles (RBAC). Cada usuario tiene un rol que determina a que modulos y acciones puede acceder.

\subsection{Matriz de Permisos Completa}

{\small
\begin{tabularx}{\textwidth}{l|c|c|c|c}
    \toprule
    \textbf{Modulo / Accion} & \rol{Admin} & \rol{Gerente} & \rol{Almacen} & \rol{Ventas} \\
    \midrule
    \multicolumn{5}{l}{\textbf{Usuarios}} \\
    \hspace{1em}Ver usuarios & \checkmark & \checkmark & & \\
    \hspace{1em}Crear usuarios & \checkmark & \checkmark & & \\
    \hspace{1em}Editar usuarios & \checkmark & \checkmark & & \\
    \hspace{1em}Eliminar/Desactivar & \checkmark & & & \\
    \midrule
    \multicolumn{5}{l}{\textbf{Productos}} \\
    \hspace{1em}Ver productos & \checkmark & \checkmark & \checkmark & \checkmark \\
    \hspace{1em}Crear productos & \checkmark & \checkmark & & \\
    \hspace{1em}Editar productos & \checkmark & \checkmark & & \\
    \hspace{1em}Eliminar productos & \checkmark & \checkmark & & \\
    \midrule
    \multicolumn{5}{l}{\textbf{Ventas}} \\
    \hspace{1em}Ver ventas & \checkmark & \checkmark & & \checkmark \\
    \hspace{1em}Crear ventas & \checkmark & \checkmark & & \checkmark \\
    \hspace{1em}Editar ventas & \checkmark & \checkmark & & \\
    \hspace{1em}Cancelar ventas & \checkmark & \checkmark & & \\
    \midrule
    \multicolumn{5}{l}{\textbf{Pedidos (Almacen)}} \\
    \hspace{1em}Ver pedidos & \checkmark & \checkmark & \checkmark & \\
    \hspace{1em}Crear pedidos & \checkmark & \checkmark & \checkmark & \\
    \hspace{1em}Editar pedidos & \checkmark & \checkmark & \checkmark & \\
    \hspace{1em}Eliminar pedidos & \checkmark & \checkmark & & \\
    \hspace{1em}Recibir mercaderia & \checkmark & \checkmark & \checkmark & \\
    \midrule
    \multicolumn{5}{l}{\textbf{Mermas}} \\
    \hspace{1em}Ver mermas & \checkmark & \checkmark & \checkmark & \\
    \hspace{1em}Registrar mermas & \checkmark & \checkmark & \checkmark & \\
    \hspace{1em}Eliminar mermas & \checkmark & & & \\
    \midrule
    \multicolumn{5}{l}{\textbf{Reportes}} \\
    \hspace{1em}Exportar datos & \checkmark & \checkmark & & \checkmark \\
    \midrule
    \multicolumn{5}{l}{\textbf{Log de Actividad}} \\
    \hspace{1em}Ver actividad & \checkmark & \checkmark & & \\
    \bottomrule
\end{tabularx}
}

\subsection{Descripcion de Roles}

\subsubsection{Administrador}
El rol con mayor nivel de acceso. Puede gestionar todos los aspectos del sistema incluyendo la creacion y eliminacion de usuarios. Recomendado para el dueno del negocio o responsable de TI.

\subsubsection{Gerente}
Acceso amplio a ventas, productos y almacen. Puede crear usuarios pero no eliminarlos. Tiene acceso al log de actividad para monitorear operaciones. Ideal para encargados de tienda.

\subsubsection{Almacen}
Enfocado en operaciones de bodega: pedidos, recepcion, mermas y vencimientos. No tiene acceso a ventas ni gestion de usuarios. Recomendado para el personal de bodega.

\subsubsection{Ventas}
Rol basico para vendedores. Puede crear y ver ventas, consultar productos y exportar reportes basicos. No tiene acceso a operaciones de almacen ni administracion.

\begin{warningbox}
    Los permisos son estrictos: si un usuario intenta acceder a una funcion no permitida para su rol, recibira un mensaje de ``Acceso Denegado'' y la accion sera registrada en el log de actividad.
\end{warningbox}
```

**Step 2: Commit**

```bash
git add ___documentos/guia_usuario/capitulos/09_roles.tex
git commit -m "feat: add roles and permissions chapter for user guide"
```

---

### Task 12: Capitulo 10 - FAQ y Solucion de Problemas

**Files:**
- Create: `___documentos/guia_usuario/capitulos/10_faq.tex`

**Step 1: Escribir capitulo de FAQ**

```latex
\section{Preguntas Frecuentes y Solucion de Problemas}
\label{sec:faq}

\subsection{Preguntas Frecuentes}

\subsubsection{Como agrego stock a un producto?}

El stock \textbf{no se ingresa directamente} en el producto. Para agregar stock debe:
\begin{enumerate}[leftmargin=2em]
    \item Crear un pedido a proveedor en \menu{Almacen > Pedidos}
    \item Confirmar la recepcion en \menu{Almacen > Recepcion}
    \item Al confirmar, se crea un lote y el stock se actualiza automaticamente
\end{enumerate}

Consulte la Seccion~\ref{subsec:recepcion} para instrucciones detalladas.

\subsubsection{Por que un producto muestra stock 0 si acabo de crearlo?}

Los productos nuevos no tienen lotes asociados. El stock total es la suma de todos los lotes del producto. Necesita realizar una \textbf{recepcion de mercaderia} para crear el primer lote.

\subsubsection{Que significa FIFO?}

FIFO significa ``First In, First Out'' (Primero en Entrar, Primero en Salir). Cuando se realiza una venta o merma, el sistema automaticamente descuenta del lote mas antiguo primero, asegurando la rotacion correcta del inventario.

\subsubsection{Puedo revertir una venta cancelada?}

No de forma automatica. Si cancela una venta, el stock \textbf{no se devuelve} automaticamente. Debe registrar una nueva recepcion con las cantidades correspondientes.

\subsubsection{Que pasa si elimino un registro de merma?}

Eliminar un registro de merma elimina el registro del historial, pero \textbf{no revierte} la deduccion de stock. El stock no se restaura automaticamente.

\subsubsection{Como cambio mi contrasena?}

Vaya a \menu{Configuracion} desde el menu lateral e ingrese su contrasena actual junto con la nueva. Consulte la Seccion~\ref{sec:login}.

\subsubsection{Puedo tener varios tenants?}

Si, SIPUD es multi-tenant. Puede cambiar de tenant desde el selector en la barra de navegacion (si tiene acceso a multiples tenants).

\subsection{Solucion de Problemas}

\subsubsection{No puedo iniciar sesion}

\begin{itemize}[leftmargin=2em]
    \item Verifique que su nombre de usuario y contrasena son correctos
    \item Confirme que su cuenta esta \textbf{activa} (consulte con un administrador)
    \item Limpie la cache del navegador e intente nuevamente
    \item Si olvido su contrasena, use la opcion ``Olvide mi contrasena''
\end{itemize}

\subsubsection{El sistema muestra ``Acceso Denegado''}

Su rol no tiene permisos para la accion que intenta realizar. Consulte la tabla de permisos en la Seccion~\ref{sec:roles} o contacte a un administrador.

\subsubsection{No aparecen productos al crear una venta}

\begin{itemize}[leftmargin=2em]
    \item Verifique que existen productos creados en el sistema
    \item Confirme que los productos tienen stock disponible (stock > 0)
    \item Revise que esta en el tenant correcto
\end{itemize}

\subsubsection{Error al exportar reportes}

\begin{itemize}[leftmargin=2em]
    \item Verifique que tiene el permiso de exportacion (\texttt{reports:export})
    \item Asegurese de que no hay bloqueadores de descargas activos en su navegador
    \item Si el archivo no se descarga, intente con otro navegador
\end{itemize}

\subsubsection{Los datos no se actualizan en pantalla}

\begin{itemize}[leftmargin=2em]
    \item Recargue la pagina con \tecla{F5} o \tecla{Ctrl+R}
    \item Limpie la cache del navegador (\tecla{Ctrl+Shift+Del})
    \item Verifique su conexion a internet/red
\end{itemize}

\subsection{Contacto de Soporte}

Si experimenta problemas no cubiertos en esta guia, contacte al administrador del sistema proporcionando:

\begin{enumerate}[leftmargin=2em]
    \item Descripcion detallada del problema
    \item Captura de pantalla del error (si aplica)
    \item Pasos para reproducir el problema
    \item Su nombre de usuario y rol
    \item Navegador y version que utiliza
\end{enumerate}
```

**Step 2: Commit**

```bash
git add ___documentos/guia_usuario/capitulos/10_faq.tex
git commit -m "feat: add FAQ chapter for user guide"
```

---

### Task 13: Crear script de captura de pantallas (placeholder)

**Files:**
- Create: `___documentos/guia_usuario/scripts/capturar_pantallas.py`

**Step 1: Crear script de captura**

```python
#!/usr/bin/env python3
"""
Script para capturar pantallazos de SIPUD automaticamente.

Requisitos:
    pip install selenium webdriver-manager

Uso:
    python capturar_pantallas.py

El script:
1. Abre un navegador Chrome automatizado
2. Navega a cada pantalla de SIPUD
3. Captura screenshots y los guarda en ../imagenes/
"""
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configuracion
BASE_URL = "http://localhost:5006"
USERNAME = "admin"
PASSWORD = "admin"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "imagenes")

# Pantallas a capturar
SCREENSHOTS = [
    ("login.png", "/login", False),
    ("dashboard_admin.png", "/", True),
    ("productos_lista.png", "/products", True),
    ("ventas_lista.png", "/sales", True),
    ("almacen_dashboard.png", "/warehouse/dashboard", True),
    ("almacen_pedidos.png", "/warehouse/orders", True),
    ("almacen_recepcion.png", "/warehouse/receiving", True),
    ("almacen_mermas.png", "/warehouse/wastage", True),
    ("almacen_vencimientos.png", "/warehouse/expiry", True),
    ("admin_usuarios.png", "/admin/users", True),
    ("admin_actividad.png", "/admin/activity", True),
]


def setup_driver():
    """Configura el driver de Chrome."""
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--hide-scrollbars")
    driver = webdriver.Chrome(options=options)
    return driver


def login(driver):
    """Inicia sesion en SIPUD."""
    driver.get(f"{BASE_URL}/login")
    time.sleep(1)

    username_field = driver.find_element(By.NAME, "username")
    password_field = driver.find_element(By.NAME, "password")

    username_field.send_keys(USERNAME)
    password_field.send_keys(PASSWORD)

    submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    submit_btn.click()
    time.sleep(2)


def capture_screenshots(driver):
    """Captura todas las pantallas definidas."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for filename, path, needs_auth in SCREENSHOTS:
        try:
            if not needs_auth and "login" in path:
                # Para login, cerrar sesion primero si esta autenticado
                driver.delete_all_cookies()
                driver.get(f"{BASE_URL}{path}")
            else:
                driver.get(f"{BASE_URL}{path}")

            time.sleep(2)  # Esperar carga completa

            filepath = os.path.join(OUTPUT_DIR, filename)
            driver.save_screenshot(filepath)
            print(f"  Capturado: {filename}")

        except Exception as e:
            print(f"  Error capturando {filename}: {e}")


def main():
    print("=== Captura automatica de pantallas SIPUD ===\n")
    print(f"URL base: {BASE_URL}")
    print(f"Directorio de salida: {OUTPUT_DIR}\n")

    driver = setup_driver()
    try:
        # Capturar login primero (sin autenticacion)
        driver.get(f"{BASE_URL}/login")
        time.sleep(2)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        driver.save_screenshot(os.path.join(OUTPUT_DIR, "login.png"))
        print("  Capturado: login.png")

        # Login y capturar el resto
        login(driver)
        print("  Sesion iniciada correctamente\n")

        for filename, path, needs_auth in SCREENSHOTS:
            if filename == "login.png":
                continue  # Ya fue capturado
            try:
                driver.get(f"{BASE_URL}{path}")
                time.sleep(2)
                filepath = os.path.join(OUTPUT_DIR, filename)
                driver.save_screenshot(filepath)
                print(f"  Capturado: {filename}")
            except Exception as e:
                print(f"  Error en {filename}: {e}")

    finally:
        driver.quit()

    print("\n=== Captura completada ===")


if __name__ == "__main__":
    main()
```

**Step 2: Commit**

```bash
git add ___documentos/guia_usuario/scripts/capturar_pantallas.py
git commit -m "feat: add screenshot capture script for user guide"
```

---

### Task 14: Crear placeholders de imagenes y compilar

**Files:**
- Create: placeholder images in `___documentos/guia_usuario/imagenes/`

**Step 1: Crear archivo .gitkeep para el directorio de imagenes**

```bash
touch ___documentos/guia_usuario/imagenes/.gitkeep
```

**Step 2: Compilar el documento LaTeX**

```bash
cd ___documentos/guia_usuario
pdflatex main.tex
pdflatex main.tex  # Segunda pasada para TOC y referencias
```

**Step 3: Verificar que el PDF se genera correctamente**

Abrir `___documentos/guia_usuario/main.pdf` y verificar:
- Portada con titulo y logo
- Tabla de contenidos con links funcionales
- Todos los capitulos presentes
- Cajas informativas con formato correcto
- Placeholders de imagenes visibles
- Numeracion de paginas en encabezados/pies

**Step 4: Commit**

```bash
git add ___documentos/guia_usuario/
git commit -m "feat: complete LaTeX user guide with all chapters and build"
```

---

## Notas de Compilacion

### Requisitos LaTeX

Para compilar el documento se necesitan los siguientes paquetes (instalables via TeX Live o MiKTeX):

```bash
# macOS con Homebrew
brew install --cask mactex

# O version ligera
brew install --cask basictex
sudo tlmgr install tcolorbox pgf environ etoolbox \
    fontawesome5 enumitem tabularx booktabs fancyhdr \
    titlesec tocloft pifont listings caption float babel-spanish
```

### Comando de compilacion

```bash
cd ___documentos/guia_usuario
pdflatex main.tex && pdflatex main.tex
```

(Se ejecuta dos veces para que la tabla de contenidos y las referencias cruzadas se resuelvan correctamente.)

### Para agregar capturas de pantalla reales

1. Asegurese de que SIPUD esta corriendo en `localhost:5006`
2. Instale Selenium: `pip install selenium webdriver-manager`
3. Ejecute el script: `python scripts/capturar_pantallas.py`
4. Recompile el PDF: `pdflatex main.tex && pdflatex main.tex`

Las capturas se guardaran en `imagenes/` y el documento las incluira automaticamente en lugar de los placeholders.
