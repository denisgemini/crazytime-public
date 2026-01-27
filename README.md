# 🎰 CrazyTime System v2.5 - Professional Dashboard & Analytics

Sistema avanzado de monitoreo en tiempo real, análisis de latidos y orquestación de datos para Crazy Time. Diseñado para ejecutarse 24/7 en infraestructuras de baja latencia (GCP Free Tier / Linux PRoot).

## 🚀 Novedades de la v2.5
*   **Heartbeat Model 2.0:** Medición ultra-precisa del tiempo entre tiros (`started_at` vs `settled_at`).
*   **Chronological Integrity:** Lógica de inserción inteligente que reubica tiros desordenados en su "espacio-tiempo" real.
*   **Pseudo-ID System:** Capa de abstracción SQL que garantiza una secuencia cronológica perfecta (1, 2, 3...) sin importar fallos de la API.
*   **Neon Dashboard:** Interfaz web modular (FastAPI + JS) con anillos de progreso neón (Azul Celeste) y alertas visuales inteligentes.

## 🛠️ Arquitectura del Sistema
*   **Backend:** FastAPI (Python 3.11+) con soporte para WebSockets/Polling.
*   **Frontend:** Vanilla JS Modular (Arquitectura State-Controller-Render).
*   **Base de Datos:** SQLite con modo WAL y Vistas Materializadas para analítica.
*   **Motor de Notificaciones:** Bot de Telegram con reportes gráficos ligeros (Pillow).

## 📊 Componentes Clave

### 📡 Colector Inteligente (`core/database.py`)
Implementa un filtro de duplicados de ±10s con búsqueda inversa (New-to-Old) y cálculo de latido contra el vecino cronológico real. Detecta y loguea anomalías de tiempo automáticamente para asegurar la calidad de los datos.

### 💻 Dashboard Modular (`dashboard/`)
*   **Real-time Ticker:** Cinta de resultados con historial fluido de los últimos tiros.
*   **Progress Rings:** Indicadores visuales de umbral (Crazy Time 190) con cambio dinámico a **Azul Celeste Neón** al alcanzar el objetivo de apuesta.
*   **Analytics Grid:** Distancias y estadísticas de patrones VIP (Pachinko/CrazyTime) actualizadas cada 3 segundos.

### 📈 Reportes Automáticos (`scripts/`)
*   Generación de gráficos de "Salud de Latidos" mediante **Pillow** (optimizado para sistemas con pocos recursos).
*   Resúmenes diarios enviados vía Telegram con métricas de eficiencia y archivos CSV adjuntos.

## 🔧 Instalación y Uso

### Ejecución del Servicio
```bash
# Iniciar el motor de recolección (Main Service)
python3 main.py

# Iniciar el Dashboard (Web Server)
python3 dashboard/app.py
```

### Comandos de Auditoría
```bash
# Ver integridad de la secuencia cronológica y Pseudo IDs
sqlite3 data/db.sqlite3 "SELECT * FROM tiros_ordenados ORDER BY pseudo_id DESC LIMIT 20"
```

## ⚠️ Disclaimer
Este sistema es para análisis estadístico y educativo. Los juegos de casino tienen un componente de azar. Los patrones detectados NO garantizan resultados futuros. Juega responsablemente.