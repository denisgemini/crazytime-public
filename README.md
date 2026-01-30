# 🎰 CrazyTime Analytics System

<div align="center">

![Version](https://img.shields.io/badge/version-2.6-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![SQLite](https://img.shields.io/badge/SQLite-WAL-orange.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Status](https://img.shields.io/badge/status-production-success.svg)

**Sistema profesional de monitoreo, análisis estadístico y alertas en tiempo real para Evolution Gaming's Crazy Time**

[Características](#-características-principales) • [Instalación](#-instalación) • [Uso](#-uso) • [Arquitectura](#-arquitectura) • [API](#-api--dashboard)

</div>

---

## 📋 Tabla de Contenidos

- [Descripción](#-descripción)
- [Características Principales](#-características-principales)
- [Arquitectura del Sistema](#-arquitectura-del-sistema)
- [Requisitos](#-requisitos)
- [Instalación](#-instalación)
- [Configuración](#-configuración)
- [Uso](#-uso)
- [API & Dashboard](#-api--dashboard)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Módulos Principales](#-módulos-principales)
- [Troubleshooting](#-troubleshooting)
- [Roadmap](#-roadmap)
- [Contribución](#-contribución)
- [Licencia](#-licencia)

---

## 🎯 Descripción

**CrazyTime Analytics System** es una plataforma de análisis avanzado diseñada para recopilar, procesar y analizar datos históricos del juego Crazy Time de Evolution Gaming. El sistema ofrece:

- 📊 **Tracking en tiempo real** de patrones y secuencias
- 🚨 **Sistema de alertas inteligente** vía Telegram
- 📈 **Análisis de ventanas de rentabilidad** (ROI/Win Rate)
- 🎯 **Detección de umbrales críticos** personalizables
- 💾 **Persistencia robusta** con SQLite WAL mode
- 🌐 **Dashboard web interactivo** con FastAPI

Optimizado para **ejecución 24/7 en entornos de bajos recursos** (GCP Free Tier, Raspberry Pi, VPS económicos).

---

## ✨ Características Principales

### 🔄 Recolección de Datos
- ✅ Polling automático cada **5 minutos** (configurable)
- ✅ Filtrado inteligente de duplicados con ventana de ±10 segundos
- ✅ Cálculo preciso de **latidos** (tiempo entre tiros)
- ✅ Captura de metadata completa (multiplicadores, flappers, top slots)
- ✅ Recuperación automática ante interrupciones de red
- ✅ Detección y recuperación de brechas de datos

### 📊 Análisis y Tracking
- ✅ Tracking de distancias para **patrones simples y secuencias**
- ✅ Persistencia de estado en **SQLite** (tabla `system_state`)
- ✅ Análisis histórico de **ventanas de apuesta** con métricas ROI/WinRate
- ✅ Detección de anomalías en latidos (diagnóstico de conexión)
- ✅ Reportes diarios automatizados con gráficos
- ✅ IDs cronológicos inmutables para integridad de datos

### 🚨 Sistema de Alertas
- ✅ Alertas multinivel por **umbral de distancia**
- ✅ Notificaciones de **patrón detectado** en zona de apuesta
- ✅ Integración con **Telegram Bot**
- ✅ Formato HTML enriquecido con detalles del tiro
- ✅ Prevención de duplicados con memoria de estado
- ✅ Alertas de HIT con métricas completas (multiplicadores, flappers)

### 🌐 Dashboard Web
- ✅ API REST con **FastAPI**
- ✅ Visualización en tiempo real del estado del sistema
- ✅ Consulta de estadísticas históricas por día
- ✅ Exportación de datos en JSON
- ✅ Documentación automática con Swagger UI

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    CRAZYTIME SYSTEM v2.6                    │
│                  SQLite-First Architecture                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
          ┌───────────────────────────────────────┐
          │         main.py (Scheduler)           │
          │   Orquestador principal del sistema   │
          │      • Ciclos cada 5 minutos          │
          │      • Recuperación de brechas        │
          │      • Logging estructurado           │
          └───────────────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            │                 │                 │
            ▼                 ▼                 ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │ DataCollector│  │PatternTracker│  │ AlertManager │
    │              │  │              │  │              │
    │ • API Client │  │ • Distancias │  │ • Umbrales   │
    │ • Filtros    │  │ • Secuencias │  │ • HIT Logic  │
    │ • Latidos    │  │ • Estado SQL │  │ • Telegram   │
    └──────────────┘  └──────────────┘  └──────────────┘
            │                 │                 │
            └─────────────────┼─────────────────┘
                              ▼
                    ┌──────────────────┐
                    │   SQLite (WAL)   │
                    │  ┌────────────┐  │
                    │  │   tiros    │  │ ← Fuente de verdad
                    │  │            │  │   • IDs inmutables
                    │  │            │  │   • Metadata completa
                    │  ├────────────┤  │
                    │  │system_state│  │ ← Estado persistente
                    │  │            │  │   • Tracker state
                    │  │            │  │   • Alert memory
                    │  └────────────┘  │
                    └──────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            │                 │                 │
            ▼                 ▼                 ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │WindowAnalyzer│  │TelegramNotif.│  │   Dashboard  │
    │              │  │              │  │              │
    │ • Histórico  │  │ • Bot API    │  │ • FastAPI    │
    │ • ROI/WinRate│  │ • HTML Rich  │  │ • REST API   │
    │ • Ventanas   │  │ • Retry Logic│  │ • Swagger UI │
    └──────────────┘  └──────────────┘  └──────────────┘
```

### Flujo de Datos

1. **Recolección** → `DataCollector` consulta API cada 5 min
2. **Validación** → Filtro de duplicados (±10s) + cálculo de latidos
3. **Almacenamiento** → Inserción en tabla `tiros` (SQLite WAL)
4. **Tracking** → `PatternTracker` actualiza estado en `system_state`
5. **Análisis** → `AlertManager` lee estado y evalúa umbrales
6. **Notificación** → Envío de alertas vía Telegram si aplica
7. **Visualización** → Dashboard consulta estado en tiempo real

### Principios de Diseño

- **SQLite-First:** Toda la persistencia crítica en base de datos
- **Idempotencia:** Reiniciar el sistema no afecta el estado
- **IDs Inmutables:** Primary keys como fuente de verdad cronológica
- **Estado Centralizado:** Tabla `system_state` como única fuente de verdad
- **Tolerancia a Fallos:** Recuperación automática de brechas y errores de red

---

## 🔧 Requisitos

### Sistema Operativo
- **Linux** (Debian/Ubuntu recomendado)
- **macOS** 10.15+
- **Windows** 10+ (con WSL2 recomendado)

### Software Requerido
```bash
Python 3.11+
SQLite 3.35+
Git
```

### Recursos Mínimos
| Recurso | Mínimo | Recomendado |
|---------|--------|-------------|
| **RAM** | 512 MB | 1 GB |
| **Disco** | 1 GB | 5 GB |
| **CPU** | 1 core @ 1 GHz | 2 cores @ 2 GHz |
| **Red** | 128 kbps | 512 kbps |

### Dependencias Python
```
requests>=2.31.0          # HTTP client
python-dotenv>=1.0.0      # Variables de entorno
python-telegram-bot>=20.7 # Telegram integration
openpyxl>=3.1.0          # Excel reports
Pillow>=10.0.0           # Image processing
fastapi>=0.104.0         # API REST (dashboard)
uvicorn>=0.24.0          # ASGI server (dashboard)
```

---

## 📦 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/denisgemini/crazytime-public.git
cd crazytime-public
```

### 2. Crear entorno virtual

```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Crear estructura de directorios

```bash
mkdir -p data/{logs,backups,analytics}
```

### 5. Verificar instalación

```bash
# Verificar Python
python3 --version  # Debe ser >= 3.11

# Verificar SQLite
python3 -c "import sqlite3; print('SQLite:', sqlite3.sqlite_version)"

# Verificar dependencias
pip list | grep -E "requests|dotenv|telegram|openpyxl|Pillow"
```

**Salida esperada:**
```
SQLite: 3.42.0
python-dotenv         1.0.0
python-telegram-bot   20.7
requests              2.31.0
openpyxl              3.1.2
Pillow                10.1.0
```

---

## ⚙️ Configuración

### 1. Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```bash
cp .env.example .env
nano .env  # o tu editor favorito
```

**Contenido de `.env`:**
```bash
# Telegram Bot Configuration
TELEGRAM_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz123456789
TELEGRAM_CHAT_ID=-1001234567890

# Database Configuration
DB_PATH=data/db.sqlite3

# System Configuration
DEBUG=False
```

#### Obtener credenciales de Telegram

**Paso 1: Crear un bot**
1. Abre Telegram y busca [@BotFather](https://t.me/botfather)
2. Envía el comando `/newbot`
3. Sigue las instrucciones (nombre del bot, username)
4. **Copia el token** que te proporciona (ej: `1234567890:ABCdef...`)

**Paso 2: Obtener tu Chat ID**
1. Busca [@userinfobot](https://t.me/userinfobot) en Telegram
2. Inicia conversación con el bot
3. **Copia tu ID** (ej: `-1001234567890` para grupos)

**Paso 3: Verificar configuración**
```bash
python3 scripts/test_telegram.py
```

**Salida esperada:**
```
✅ Conexión exitosa con Telegram
📤 Mensaje de prueba enviado correctamente
```

### 2. Configuración de Patrones

Edita `config/patterns.py` para personalizar patrones monitoreados:

```python
from config.patterns import Pattern

# Ejemplo: Configurar Pachinko
PACHINKO = Pattern(
    id="pachinko",
    name="Pachinko",
    type="simple",
    value="Pachinko",
    
    # Umbrales de AVISO (solo notificación)
    warning_thresholds=[50, 110],
    
    # Ventanas de APUESTA (reportes de HIT)
    betting_windows=[
        (61, 90),    # Ventana 1: distancias 61-90
        (121, 150)   # Ventana 2: distancias 121-150
    ],
    
    alert_level="vip",
    description="Bonus game con multiplicadores"
)
```

**Patrones disponibles por defecto:**
- `pachinko` - Bonus Pachinko
- `crazytime` - Bonus Crazy Time
- `numero_10` - Número 10
- `secuencia_2_5` - Secuencia 2→5
- `secuencia_5_2` - Secuencia 5→2

### 3. Inicialización de Base de Datos

La base de datos se crea automáticamente en el primer arranque:

```bash
python3 main.py
```

**Verificación manual del schema:**
```bash
sqlite3 data/db.sqlite3 << EOF
.schema tiros
.schema system_state
PRAGMA journal_mode;
EOF
```

**Salida esperada:**
```sql
CREATE TABLE tiros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resultado TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    started_at TEXT,
    settled_at TEXT,
    latido INTEGER DEFAULT 0,
    ...
);

CREATE TABLE system_state (
    module TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (module, key)
);

wal
```

---

## 🚀 Uso

### Modo Servicio (Producción)

Inicia el recolector en segundo plano:

```bash
# Activar entorno
source venv/bin/activate

# Iniciar servicio
python3 main.py
```

**Salida esperada:**
```
INFO - ======================================================================
INFO - 🚀 CRAZYTIME SERVICE v2.6 - INICIANDO
INFO - ======================================================================
INFO - Modo: Servicio persistente 24/7
INFO - Intervalo: 5 minutos
INFO - Plataforma: Google Cloud Platform Free Tier
INFO - ======================================================================
INFO - ✅ Integridad de BD verificada
INFO - ✅ Bot de Telegram inicializado con timeouts robustos
INFO - ✅ Scheduler inicializado correctamente
INFO - 📤 Mensaje enviado a Telegram
INFO -
======================================================================
INFO - 🔄 CICLO #1 - 2026-01-29 23:14:27
INFO - ======================================================================
INFO - 📊 Procesando tracking de distancias...
INFO - ✅ Tracking: 6 tiros procesados
INFO - 🚨 Evaluando alertas...
INFO - ✅ Sin alertas que enviar
INFO - ⏳ Esperando 5 minutos hasta próximo ciclo...
```

### Dashboard Web

Inicia el servidor web para visualización:

```bash
# En una terminal separada
source venv/bin/activate
python3 dashboard/app.py
```

**Salida esperada:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Abre en tu navegador: **`http://localhost:8000`**

### Scripts de Análisis

```bash
# Análisis de latidos (salud de conexión)
python3 scripts/analyze_latidos.py

# Reporte diario con gráficos
python3 analytics/daily_report.py

# Análisis de ventanas de rentabilidad
python3 scripts/analyze_windows.py

# Forzar reporte diario (ignora cooldown)
python3 scripts/force_daily_summary.py
```

### Instalación como Servicio Systemd (Linux)

Para ejecución automática al inicio del sistema:

```bash
# Editar script de instalación
nano scripts/install_service.sh

# Ejecutar instalador
sudo bash scripts/install_service.sh

# Verificar estado
sudo systemctl status crazytime

# Ver logs en tiempo real
sudo journalctl -u crazytime -f
```

---

## 📊 API & Dashboard

### REST API Endpoints

#### `GET /api/stats`
Obtiene estadísticas generales del sistema (últimas 24h).

**Request:**
```bash
curl http://localhost:8000/api/stats
```

**Response:**
```json
{
  "total_spins": 15234,
  "range_start": "2026-01-28T23:00:00",
  "range_end": "2026-01-29T23:00:00",
  "counts": {
    "1": 4521,
    "2": 3012,
    "5": 2145,
    "10": 1834,
    "CoinFlip": 1245,
    "CashHunt": 967,
    "Pachinko": 892,
    "CrazyTime": 156
  },
  "latidos": {
    "5s": 12450,
    "0_4s": 1234,
    "6_11s": 892,
    "gt11s": 456,
    "neg": 2
  }
}
```

#### `GET /api/patterns/{pattern_id}`
Estado en tiempo real de un patrón específico.

**Request:**
```bash
curl http://localhost:8000/api/patterns/pachinko
```

**Response:**
```json
{
  "pattern_id": "pachinko",
  "last_id": 5023,
  "last_distance": 0,
  "prev_distance": 67,
  "updated_at": "2026-01-29T23:10:15"
}
```

**Interpretación:**
- `last_id`: ID del último tiro donde salió el patrón
- `last_distance`: Distancia actual (0 si acaba de salir)
- `prev_distance`: Distancia del hit anterior

#### `GET /api/windows/{pattern_id}`
Análisis de ventanas de rentabilidad.

**Request:**
```bash
curl http://localhost:8000/api/windows/pachinko
```

**Response:**
```json
{
  "pattern": "Pachinko",
  "windows": [
    {
      "range": [61, 90],
      "win_rate": 62.5,
      "roi": -53.1,
      "sample_size": 48,
      "avg_multiplier": 8.4
    },
    {
      "range": [121, 150],
      "win_rate": 0.0,
      "roi": 0.0,
      "sample_size": 8,
      "avg_multiplier": 0
    }
  ],
  "total_analyzed": 156
}
```

#### `GET /docs`
Documentación interactiva Swagger UI.

Abre: **`http://localhost:8000/docs`**

---

## 📁 Estructura del Proyecto

```
crazytime-public/
│
├── 📄 main.py                    # Punto de entrada principal
├── 📄 requirements.txt           # Dependencias Python
├── 📄 .env.example              # Plantilla de variables de entorno
├── 📄 README.md                 # Este archivo
├── 📄 GEMINI.md                 # Notas de desarrollo
│
├── 📁 config/
│   └── patterns.py              # Definición de patrones VIP
│
├── 📁 core/                     # Módulos principales
│   ├── __init__.py
│   ├── database.py              # Capa de acceso a SQLite
│   ├── collector.py             # Recolector de datos de API
│   └── api_client.py            # Cliente HTTP para API externa
│
├── 📁 analytics/                # Módulos de análisis
│   ├── __init__.py
│   ├── pattern_tracker.py       # Tracking de distancias
│   ├── window_analyzer.py       # Análisis de ventanas ROI
│   └── daily_report.py          # Generador de reportes diarios
│
├── 📁 alerting/                 # Sistema de alertas
│   ├── __init__.py
│   ├── alert_manager.py         # Gestor de alertas y umbrales
│   └── notification.py          # Integración Telegram
│
├── 📁 orchestration/            # Orquestación del sistema
│   ├── __init__.py
│   └── scheduler.py             # Coordinador de ciclos
│
├── 📁 dashboard/                # API REST y Web UI
│   ├── app.py                   # FastAPI application
│   ├── check_paths.py           # Verificador de rutas estáticas
│   ├── 📁 static/               # CSS, JS, imágenes
│   └── 📁 templates/            # HTML templates
│
├── 📁 scripts/                  # Scripts auxiliares
│   ├── __init__.py
│   ├── analyze_latidos.py       # Auditoría de latidos
│   ├── analyze_windows.py       # Análisis de ventanas
│   ├── analyze_durations.py     # Análisis de duraciones
│   ├── auto_backup.py           # Sistema de backups
│   ├── force_daily_summary.py   # Forzar reporte diario
│   ├── test_telegram.py         # Test de Telegram Bot
│   └── install_service.sh       # Instalador systemd
│
├── 📁 assets/                   # Recursos gráficos
│   ├── logo.jpg
│   ├── pachinko.png
│   ├── crazytime.png
│   ├── 10.png
│   ├── 2-5.png
│   └── 5-2.png
│
└── 📁 data/                     # Datos persistentes (gitignored)
    ├── db.sqlite3               # Base de datos principal
    ├── db.sqlite3-wal           # Write-Ahead Log
    ├── db.sqlite3-shm           # Shared memory
    ├── bitacora_brechas.csv     # Log de brechas detectadas
    ├── 📁 logs/                 # Logs del sistema
    ├── 📁 backups/              # Backups automáticos
    └── 📁 analytics/            # Reportes generados
```

---

## 🧩 Módulos Principales

### `core/database.py`
**Capa de acceso a datos con SQLite.**

**Responsabilidades:**
- Gestión de conexiones con WAL mode
- Schema de tablas `tiros` y `system_state`
- Operaciones CRUD optimizadas
- Persistencia de estado del sistema
- Cálculo de estadísticas agregadas

**Métodos clave:**
```python
# Inserción de datos
db.insertar_datos(datos: list[dict]) -> int

# Consultas
db.get_spins_after_id(after_id: int) -> list[dict]
db.get_spin_by_id(spin_id: int) -> Optional[dict]
db.get_last_spin() -> Optional[dict]

# Estado del sistema
db.get_state(module: str, key: str, default=None)
db.set_state(module: str, key: str, value)

# Estadísticas
db.obtener_estadisticas_dia(fecha: Optional[str]) -> dict
```

### `core/collector.py`
**Recolector de datos desde API externa.**

**Responsabilidades:**
- Polling cada 5 minutos
- Parseo de respuestas JSON
- Detección de brechas en datos
- Recuperación automática ante fallos
- Filtrado de duplicados

**Métodos clave:**
```python
collector.fetch_batches() -> list[list[dict]]
collector.fetch_and_store() -> int
```

### `analytics/pattern_tracker.py`
**Motor de tracking de patrones.**

**Responsabilidades:**
- Procesamiento secuencial de tiros
- Cálculo de distancias entre apariciones
- Actualización de estado en SQLite
- Detección de secuencias multi-paso
- Memoria de último resultado

**Métodos clave:**
```python
tracker.process_new_spins() -> int
tracker.get_pattern_state(pattern_id: str) -> dict
```

**Estructura de estado:**
```python
{
    "last_id": 5023,        # ID del último hit
    "last_distance": 0,      # Distancia actual
    "prev_distance": 67      # Distancia del hit anterior
}
```

### `alerting/alert_manager.py`
**Sistema de alertas basado en umbrales.**

**Responsabilidades:**
- Evaluación de condiciones de alerta
- Prevención de duplicados
- Formateo de mensajes
- Integración con notificador
- Detección de HITs en zonas de apuesta

**Métodos clave:**
```python
alert_manager.check_all_patterns() -> list[Alert]
alert_manager.check_pattern(pattern, current_max_id, tracker_data) -> list[Alert]
```

**Tipos de alertas:**
```python
class AlertType(Enum):
    THRESHOLD_REACHED = "threshold_reached"  # Aviso de umbral
    PATTERN_HIT = "pattern_hit"              # Hit en zona de apuesta
```

### `dashboard/app.py`
**API REST y dashboard web.**

**Responsabilidades:**
- Servir endpoints RESTful
- Consultas en tiempo real a BD
- Documentación automática (Swagger)
- CORS configurado para frontend
- Serving de archivos estáticos

---

## 🐛 Troubleshooting

### Problema: Error de conexión a SQLite

**Síntoma:**
```
sqlite3.OperationalError: database is locked
```

**Causa:** La base de datos no está en modo WAL o hay un proceso bloqueando.

**Solución:**
```bash
# Verificar modo WAL
sqlite3 data/db.sqlite3 "PRAGMA journal_mode;"

# Debería retornar: wal

# Si retorna "delete", forzar WAL:
sqlite3 data/db.sqlite3 "PRAGMA journal_mode=WAL;"

# Verificar procesos que usan la BD
lsof data/db.sqlite3

# Si es necesario, matar procesos zombies
killall python3
```

---

### Problema: No se reciben alertas de Telegram

**Síntoma:**
```
⚠️ Notificador no disponible, alertas no enviadas
```

**Diagnóstico paso a paso:**

**1. Verificar `.env`:**
```bash
cat .env | grep TELEGRAM
```

**2. Probar token manualmente:**
```bash
TOKEN="tu_token_aqui"
curl https://api.telegram.org/bot$TOKEN/getMe
```

**Respuesta esperada:**
```json
{"ok":true,"result":{"id":123456789,"is_bot":true,"first_name":"YourBot"}}
```

**3. Verificar que el bot esté en el chat:**
```bash
python3 scripts/test_telegram.py
```

**4. Verificar logs del sistema:**
```bash
tail -50 data/logs/system.log | grep -i telegram
```

**Soluciones comunes:**
- Token incorrecto → Regenerar con @BotFather
- Chat ID incorrecto → Verificar con @userinfobot
- Bot no agregado al grupo → Agregar bot al grupo/canal
- Permisos insuficientes → Dar permisos de administrador al bot

---

### Problema: Duplicados en base de datos

**Síntoma:**
```
⚠️ ANOMALÍA [Filtro 10s]: Pachinko (2026-01-29T15:30:00) choca con ID #5012
```

**Explicación:**
Esto es un **WARNING informativo**, no un error. El filtro de duplicados está funcionando correctamente y previniendo la inserción.

**Interpretación:**
- El sistema detectó un tiro con timestamp muy cercano (±10s) a uno existente
- El tiro fue **rechazado** (no se insertó)
- Esto es normal cuando hay desfases en la API

**Verificación:**
```sql
SELECT id, resultado, timestamp 
FROM tiros 
WHERE id BETWEEN 5010 AND 5015 
ORDER BY id;
```

**No requiere acción** a menos que veas cientos de anomalías por hora.

---

### Problema: Latidos negativos

**Síntoma:**
```
latidos.neg > 0 en estadísticas diarias
```

**Causa:** Desfases de timestamp en la API (el tiro N+1 tiene `started_at` anterior al `settled_at` del tiro N).

**Diagnóstico:**
```bash
python3 scripts/analyze_latidos.py
```

**Salida esperada:**
```
📊 Análisis de Latidos - Últimas 1000 tiros
================================================
Total tiros: 1000
Latidos 5s (normales): 892 (89.2%)
Latidos 0-4s: 45 (4.5%)
Latidos 6-11s: 38 (3.8%)
Latidos >11s: 23 (2.3%)
Latidos negativos: 2 (0.2%) ⚠️
```

**Solución:**
- **<1% negativos:** Normal, no requiere acción
- **>5% negativos:** Posible problema con timestamps de API, verificar `api_client.py`

---

### Problema: Ciclo tarda mucho

**Síntoma:**
```
INFO - ⏳ Esperando 5 minutos hasta próximo ciclo...
[20 minutos después, aún esperando]
```

**Causa:** El proceso está bloqueado o dormido.

**Diagnóstico:**
```bash
# Ver procesos Python
ps aux | grep python3

# Ver threads activos
top -H -p $(pgrep -f main.py)

# Ver conexiones de red
netstat -tulpn | grep python
```

**Solución:**
```bash
# Reiniciar servicio
killall python3
python3 main.py

# Si persiste, verificar logs
tail -100 data/logs/system.log
```

---

### Problema: Dashboard no carga

**Síntoma:**
```
curl: (7) Failed to connect to localhost port 8000: Connection refused
```

**Diagnóstico:**

**1. Verificar que el proceso esté corriendo:**
```bash
ps aux | grep "dashboard/app.py"
```

**2. Verificar puerto:**
```bash
netstat -tulpn | grep 8000
```

**3. Probar inicio manual:**
```bash
source venv/bin/activate
python3 dashboard/app.py
```

**4. Verificar dependencias:**
```bash
pip list | grep -E "fastapi|uvicorn"
```

**Soluciones comunes:**
- Puerto ocupado → Cambiar puerto en `app.py`
- FastAPI no instalado → `pip install fastapi uvicorn`
- Permisos de firewall → Agregar regla para puerto 8000

---

### Problema: "Sistema desfasado" en reporte

**Síntoma:**
Mensaje de Telegram indica que el sistema lleva X horas sin actualizar.

**Causa:** El servicio `main.py` no está corriendo.

**Verificación:**
```bash
# Ver último tiro en BD
sqlite3 data/db.sqlite3 "SELECT id, resultado, timestamp FROM tiros ORDER BY id DESC LIMIT 1;"
```

**Solución:**
```bash
# Reiniciar servicio
python3 main.py

# Verificar que esté actualizando
tail -f data/logs/system.log
```

---

## 🗺️ Roadmap

### v2.7 (Próxima versión)
- [ ] Migrar completamente a estado SQLite (eliminar JSONs legacy)
- [ ] Dashboard interactivo con gráficos en tiempo real
- [ ] API de predicción basada en análisis histórico
- [ ] Exportación de reportes en PDF
- [ ] Soporte para múltiples usuarios/canales de Telegram

### v3.0 (Futuro)
- [ ] Machine Learning para predicción de patrones
- [ ] Multi-mesa (tracking de múltiples mesas simultáneas)
- [ ] Frontend React con visualizaciones D3.js
- [ ] Integración con Discord y Slack
- [ ] Sistema de backtesting para estrategias

### Ideas en evaluación
- [ ] Modo "paper trading" para simulación
- [ ] Integración con APIs de casinos
- [ ] Alertas por SMS (Twilio)
- [ ] Aplicación móvil (React Native)

---

## 🤝 Contribución

Las contribuciones son bienvenidas. Por favor sigue estos pasos:

### Proceso de Contribución

1. **Fork** el repositorio
2. **Crea** una rama para tu feature:
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Commit** tus cambios con mensajes descriptivos:
   ```bash
   git commit -m 'feat: Add amazing feature'
   ```
4. **Push** a la rama:
   ```bash
   git push origin feature/amazing-feature
   ```
5. Abre un **Pull Request**

### Estándares de Código

- **Style Guide:** Sigue [PEP 8](https://pep8.org/)
- **Docstrings:** Usa formato Google style
- **Type Hints:** Incluye anotaciones de tipos
- **Testing:** Añade tests para nueva funcionalidad
- **Logging:** Usa el módulo `logging`, no `print()`

### Ejemplo de Docstring

```python
def calculate_roi(window: tuple[int, int], pattern_id: str) -> float:
    """
    Calcula el ROI de una ventana de apuesta.
    
    Args:
        window: Tupla (inicio, fin) de la ventana
        pattern_id: Identificador del patrón
        
    Returns:
        ROI en porcentaje (ej: -53.1 para pérdida del 53.1%)
        
    Raises:
        ValueError: Si la ventana es inválida
    """
    pass
```

### Áreas que necesitan ayuda

- 📊 **Analytics:** Nuevos algoritmos de análisis
- 🎨 **Dashboard:** Mejoras en UI/UX
- 🧪 **Testing:** Cobertura de tests
- 📖 **Documentación:** Tutoriales y guías

---

## 📄 Licencia

Este proyecto está bajo la **Licencia MIT**. Ver archivo [`LICENSE`](LICENSE) para más detalles.

```
MIT License

Copyright (c) 2026 Denis Gemini

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 📧 Contacto

**Denis Gemini**  
GitHub: [@denisgemini](https://github.com/denisgemini)  
Email: denis.gemini@example.com (actualizar con email real)

**Project Link:** [https://github.com/denisgemini/crazytime-public](https://github.com/denisgemini/crazytime-public)

---

## 🙏 Agradecimientos

- **Evolution Gaming** - Por la API de datos de Crazy Time
- **Comunidad Python** - Por las increíbles librerías open-source
- **SQLite Team** - Por el mejor motor de BD embebido
- **FastAPI Team** - Por el framework web más rápido de Python

---

<div align="center">

**⭐ Si este proyecto te resulta útil, considera darle una estrella en GitHub ⭐**

[⬆ Volver arriba](#-crazytime-analytics-system)

</div>

