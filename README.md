# 🎰 CrazyTime Analytics System v2.0

Sistema automatizado de monitoreo y análisis del juego Crazy Time de Evolution Gaming.

## 📋 Características

### ✅ Sistema de Alertas
- **2 alertas por patrón VIP**:
  - 🟡 Umbral alcanzado (antes de ventana óptima)
  - 🎉 Patrón salió (confirmación con detalles de pago)
- **Patrones VIP con alertas**:
  - **Pachinko**: Umbrales en 50 y 110 tiros
  - **Crazy Time**: Umbrales en 190 y 250 tiros
- **Sin spam**: Sistema inteligente que evita duplicados
- **Soporte de imágenes**: Alertas con imágenes de los patrones para mejor identificación

### 📊 Análisis de Ventanas
- **Ventanas fijas**: 30 tiros, comenzando 10 tiros después del umbral
- **Análisis histórico**: ROI, hit rate, pagos promedio
- **Reportes automáticos**: JSON + Excel con datos detallados
- **Ejecución automática**: Cada ciclo verifica y actualiza los análisis

### 📈 Tracking de Distancias
- Registro completo de tiempos de espera entre apariciones
- Estadísticas: media, mediana, mín, máx
- Exportable para análisis avanzado

### 🛡️ Robustez 24/7
- Reconexión automática a la API (3 reintentos)
- Detección de brechas de servicio
- Recalibración automática después de interrupciones
- Logging completo con rotación

### 🌐 Zona Horaria
- **Servidor configurado**: America/Lima (UTC-5)
- **Resumen diario**: Se envía a las 23:55 hora Perú
- **Timestamps**: Todos en hora local del servidor

## 🚀 Instalación

### Requisitos
- Python 3.11+
- Cuenta de Telegram (bot token y chat ID)
- Conexión a internet

### Paso 1: Preparar entorno
\`\`\`bash
cd /home/denis/crazytime_v2
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
\`\`\`

### Paso 2: Configurar credenciales
\`\`\`bash
nano .env
\`\`\`

Contenido:
\`\`\`
TELEGRAM_BOT_TOKEN=tu_token_aqui
TELEGRAM_CHAT_ID=tu_chat_id_aqui
\`\`\`

### Paso 3: Ejecutar
\`\`\`bash
python main.py
\`\`\`

## 🔧 Gestión del Servicio

### Comandos Básicos
\`\`\`bash
# Ver estado
sudo systemctl status crazytime

# Iniciar
sudo systemctl start crazytime

# Detener
sudo systemctl stop crazytime

# Ver logs
sudo journalctl -u crazytime -f

# Ver logs del sistema
tail -f data/logs/system.log
\`\`\`

## 📁 Estructura del Proyecto

\`\`\`
crazytime_v2/
├── config/
│   └── patterns.py              # Configuración de patrones + PATTERN_IMAGES
├── core/
│   ├── api_client.py            # Cliente API con reintentos
│   ├── database.py              # SQLite con WAL mode
│   └── collector.py             # Recolector de datos
├── analytics/
│   ├── pattern_tracker.py       # Tracking de distancias
│   └── window_analyzer.py       # Análisis de ventanas
├── alerting/
│   ├── alert_manager.py         # Gestión de alertas
│   └── notification.py          # Telegram notifier con imágenes
├── orchestration/
│   └── scheduler.py             # Orquestador principal
├── scripts/
│   ├── auto_backup.py           # Backups 7-4-3
│   ├── analyze_windows.py       # Análisis manual
│   └── install_service.sh       # Instalador systemd
├── assets/                      # Imágenes para mensajes Telegram
│   ├── pachinko.png
│   ├── crazytime.png
│   ├── 10.png
│   ├── 2-5.png
│   ├── 5-2.png
│   └── logo.jpg
├── data/
│   ├── db.sqlite3               # Base de datos principal
│   ├── distances/               # JSONs con distancias
│   ├── analytics/               # Reportes de análisis (JSON + XLSX)
│   ├── backups/                 # Backups automáticos
│   └── logs/                    # Logs del sistema
├── main.py                      # SERVICIO (bucle infinito)
├── requirements.txt
├── .env.example
└── README.md
\`\`\`

## 📊 Análisis de Datos

### Archivos Generados

#### 1. Distancias (data/distances/)
\`\`\`json
{
  "pattern_id": "pachinko",
  "pattern_name": "Pachinko",
  "occurrences": [...],
  "distances": [65, 89, 45, 123, ...],
  "statistics": {
    "count": 45,
    "mean": 67.3,
    "median": 65,
    "min": 12,
    "max": 234
  }
}
\`\`\`

#### 2. Análisis de Ventanas (data/analytics/)

**JSON**: \`pachinko_window_analysis.json\`
\`\`\`json
{
  "pattern_name": "Pachinko",
  "thresholds": {
    "50": {
      "hit_rate": 62.2,
      "roi": 15.3,
      "total_opportunities": 45
    }
  }
}
\`\`\`

**Excel**: \`pachinko_window_analysis.xlsx\`

**Archivos generados automáticamente**:
- \`pachinko_window_analysis.json\` / \`pachinko_window_analysis.xlsx\`
- \`crazytime_window_analysis.json\` / \`crazytime_window_analysis.xlsx\`
- \`window_analysis_full.json\` (reporte consolidado)

### Análisis Manual
\`\`\`bash
source .venv/bin/activate
python scripts/analyze_windows.py
\`\`\`

## 🐛 Troubleshooting

### Error: "Telegram credentials not configured"
**Solución**: Verifica que \`.env\` existe y tiene formato correcto.

### Error: "API: Todos los reintentos fallaron"
**Solución**: Verifica conexión a internet. API puede estar caída temporalmente.

### Servicio no inicia
\`\`\`bash
# Ver error detallado
sudo journalctl -u crazytime -n 50
\`\`\`

## 🔄 Tareas Automáticas

### Resumen Diario
- **Cuándo**: 23:55-23:59 (hora Perú, UTC-5)
- **Qué envía**: Estadísticas del día por Telegram
  - Total de spins
  - Números básicos (1, 2, 5, 10)
  - Bonus rounds (Coin Flip, Cash Hunt, Pachinko, Crazy Time)

### Backup Automático
- **Frecuencia**: Cada 24 horas
- **Política de retención**: 7-4-3

## 📝 Historial de Cambios

### v2.0.1 (Enero 2026)
- ✅ Corregido timezone: Servidor en America/Lima (UTC-5)
- ✅ Soporte de imágenes en alertas de Telegram
- ✅ Análisis de ventanas automático en cada ciclo
- ✅ Reportes en Excel generados automáticamente

### v2.0.0 (Enero 2026)
- Release inicial del sistema v2.0
- Servicio persistente 24/7 con systemd
- Alertas de umbrales para Pachinko y Crazy Time
- Tracking de distancias
- Análisis de ventanas con ROI y hit rate

## 👤 Autor

**CrazyTime Analytics Team**
- Email: sigfrido1111@gmail.com
- Versión: 2.0.1
- Fecha: Enero 2026

## ⚠️ Disclaimer

Este sistema es para análisis estadístico y educativo. Los juegos de casino tienen componente de azar. Los patrones detectados NO garantizan resultados futuros. Juega responsablemente.
