# Plan: SIPUD → SIBAC (Producto Vendible)

> **SIBAC** = Sistema de Inventario Bastián Chávez
> Versión genérica, limpia y documentada para vender a otros clientes.

---

## 🎯 Objetivo

Convertir SIPUD (proyecto específico para Puerto Distribución) en SIBAC (producto SaaS multi-tenant vendible).

---

## 📋 Fases del Proyecto

### Fase 1: Auditoría de SIPUD (1-2 días)
> Revisar código actual, encontrar problemas, documentar estado.

- [ ] **1.1 Código muerto**: Encontrar funciones/rutas/templates sin usar
- [ ] **1.2 Dependencias**: Revisar requirements.txt, eliminar no usadas
- [ ] **1.3 Errores silenciosos**: Buscar try/except vacíos, logs faltantes
- [ ] **1.4 Seguridad**: Revisar tokens hardcodeados, SQL injection, XSS
- [ ] **1.5 Performance**: Queries N+1, índices faltantes en MongoDB
- [ ] **1.6 Tests**: Verificar cobertura actual (probablemente 0%)
- [ ] **1.7 Backups**: Documentar estrategia actual, verificar que funcionen

**Entregable**: `AUDIT_REPORT.md` con hallazgos y prioridades

---

### Fase 2: Limpieza de SIPUD (2-3 días)
> Arreglar lo encontrado en la auditoría.

- [ ] **2.1** Eliminar código muerto
- [ ] **2.2** Limpiar dependencias
- [ ] **2.3** Agregar logging consistente
- [ ] **2.4** Arreglar vulnerabilidades de seguridad
- [ ] **2.5** Optimizar queries lentas
- [ ] **2.6** Agregar validaciones faltantes
- [ ] **2.7** Estandarizar manejo de errores

**Entregable**: SIPUD limpio y estable

---

### Fase 3: Documentación (2-3 días)
> Documentar para que cualquier dev pueda entender y modificar.

- [ ] **3.1 README.md**: Setup, requisitos, cómo correr
- [ ] **3.2 ARCHITECTURE.md**: Estructura de carpetas, flujo de datos
- [ ] **3.3 API.md**: Documentar todos los endpoints
- [ ] **3.4 MODELS.md**: Esquemas de MongoDB explicados
- [ ] **3.5 DEPLOYMENT.md**: Cómo deployar en producción
- [ ] **3.6 Docstrings**: Agregar a funciones principales
- [ ] **3.7 CHANGELOG.md**: Historial de cambios

**Entregable**: Documentación completa en `/docs`

---

### Fase 4: Crear SIBAC (3-5 días)
> Clonar y generalizar para multi-cliente.

- [ ] **4.1** Clonar repo a `~/Proyectos/SIBAC`
- [ ] **4.2** Renombrar referencias (SIPUD → SIBAC)
- [ ] **4.3** Remover datos específicos de Puerto Distribución
- [ ] **4.4** Crear sistema de configuración por tenant
- [ ] **4.5** Agregar onboarding para nuevos clientes
- [ ] **4.6** Crear panel de super-admin (gestionar tenants)
- [ ] **4.7** Sistema de planes/límites (free, pro, enterprise)
- [ ] **4.8** Personalización de branding por tenant (logo, colores)

**Entregable**: SIBAC listo para primer cliente de prueba

---

### Fase 5: Preparar para Venta (2-3 días)
> Lo necesario para ofrecer comercialmente.

- [ ] **5.1** Landing page simple
- [ ] **5.2** Documentación para clientes (no técnica)
- [ ] **5.3** Definir precios y planes
- [ ] **5.4** Proceso de onboarding automatizado
- [ ] **5.5** Sistema de soporte/tickets básico
- [ ] **5.6** Términos de servicio y privacidad

**Entregable**: Producto listo para vender

---

## 📁 Estructura Propuesta

```
~/Proyectos/
├── SIPUD/              # Versión Puerto Distribución (cliente actual)
│   └── (mantener como está, cliente en producción)
│
└── SIBAC/              # Versión producto genérico
    ├── app/
    │   ├── routes/
    │   ├── templates/
    │   ├── models.py
    │   └── ...
    ├── docs/
    │   ├── README.md
    │   ├── API.md
    │   ├── ARCHITECTURE.md
    │   └── ...
    ├── tests/
    ├── scripts/
    │   ├── backup.py
    │   ├── seed_demo.py
    │   └── ...
    └── docker-compose.yml
```

---

## ⏱️ Estimación Total

| Fase | Tiempo estimado |
|------|-----------------|
| 1. Auditoría | 1-2 días |
| 2. Limpieza | 2-3 días |
| 3. Documentación | 2-3 días |
| 4. Crear SIBAC | 3-5 días |
| 5. Preparar venta | 2-3 días |
| **Total** | **10-16 días** |

---

## 🚀 Siguiente Paso

**Empezar con Fase 1.1**: Auditoría de código muerto.

¿Aprobado para comenzar?

---

## 📝 Notas

- SIPUD sigue en producción para Puerto Distribución
- SIBAC será el fork limpio para nuevos clientes
- Ambos pueden evolucionar en paralelo (features de SIBAC se pueden portar a SIPUD)
