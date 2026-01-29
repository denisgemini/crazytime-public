# 🎰 CrazyTime System v2.6 - Documentación de Referencia

## 🚀 Resumen del Sistema
Sistema avanzado de monitoreo y análisis estadístico para Crazy Time. Optimizado para integridad de datos 24/7 y ejecución eficiente en entornos de bajos recursos.

## 🛠️ Arquitectura Consolidada (v2.6)
- **Recolección:** Intervalo de **5 minutos** (300s) para filtrar desfases de API.
- **Base de Datos:** SQLite en modo **WAL**. Fuente de verdad: tabla `tiros`.
- **Persistencia de Estado:** Uso de tabla `system_state` en BD para garantizar que el progreso del Tracker y Alertas sobreviva a reinicios y borrados de archivos.
- **Integridad:** Uso de **IDs Reales e Inmutables** (Primary Key) para todo el flujo de análisis.
- **Tracking:** Procesamiento secuencial mediante `PatternTracker`, sincronizado con archivos JSON en `data/distances/`.
- **Frontend:** Dashboard en FastAPI que consume el estado directamente desde la tabla `system_state`.

## 📋 Componentes Principales
- `main.py`: Servicio recolector en segundo plano.
- `dashboard/app.py`: Servidor de API y Web UI.
- `analytics/daily_report.py`: Generador de reportes estratégicos festivos.
- `analytics/window_analyzer.py`: Auditoría histórica de rentabilidad de ventanas.
- `scripts/analyze_latidos.py`: Auditoría de salud de conexión y cortes de Android.

## 🔧 Comandos Rápidos
```bash
# Activar entorno
source venv/bin/activate

# Iniciar Recolector
python3 main.py

# Iniciar Dashboard
python3 dashboard/app.py

# Auditar Latidos
python3 scripts/analyze_latidos.py
```

---
*Nota: Este sistema está diseñado para la precisión cronológica total y persistencia robusta.*