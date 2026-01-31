# 🎰 CrazyTime Analytics System

<div align="center">

![Version](https://img.shields.io/badge/version-3.0-blue.svg)
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
- 🚨 **Sistema de alertas inteligente** vía Telegram (Umbrales y Hits)
- 📈 **Análisis de ventanas de rentabilidad** (ROI/Win Rate) basado en BD
- 🎯 **Detección de puntos de impacto** (Multiplicadores y Flappers)
- 💾 **Persistencia Robusta:** Arquitectura 100% SQLite (Sin archivos volátiles)
- 🌐 **Dashboard v3.0:** Monitor de guerra interactivo con FastAPI

Optimizado para **ejecución 24/7 en entornos de bajos recursos** (GCP Free Tier, Raspberry Pi, VPS económicos).

---

## ✨ Características Principales

### 🔄 Recolección de Datos
- ✅ Polling automático cada **5 minutos** (configurable)
- ✅ Filtrado inteligente de duplicados con ventana de ±10 segundos
- ✅ Cálculo preciso de **latidos** (tiempo entre tiros)
- ✅ Captura de metadata completa (multiplicadores, flappers, top slots)
- ✅ Recuperación automática ante interrupciones de red (Escalera de hasta 72h)

### 📊 Análisis y Tracking (v3.0)
- ✅ Tracking de distancias para **patrones simples y secuencias**
- ✅ **Pure SQLite:** Persistencia total en la tabla `system_state`
- ✅ Cálculo dinámico de estadísticas (Media, Mediana, Max/Min)
- ✅ Análisis histórico de **ventanas de apuesta** con métricas ROI/WinRate
- ✅ IDs cronológicos inmutables para integridad de datos absoluta

### 🚨 Sistema de Alertas
- ✅ Alertas de **Umbral de Distancia** (Avisos de calentamiento)
- ✅ Notificaciones de **HIT en zona de juego** (A partir de la 1ª ventana)
- ✅ **Lógica Anti-Pérdida:** Memoria de distancia previa para no saltar alertas en el mismo ciclo
- ✅ Formato HTML enriquecido con multiplicadores y fotos de patrones

### 🌐 Dashboard Web v3.0
- ✅ **Enfoque VIP:** Visualización exclusiva de Pachinko y Crazy Time (Sin ruido).
- ✅ **Lógica de Ventanas:** Indicadores visuales de "Zona de Espera", "Preparar" y "Zona de Juego (Neón)".
- ✅ **Indicador LIVE:** Semáforo real sincronizado con el estado del servicio (`service_running`).
- ✅ **Histograma Detallado:** 10 barras incluyendo Bonus individuales (PK, CH, CF, CT) y Secuencias (2→5, 5→2).
- ✅ **Estadísticas Neutrales:** Conteo de tiros basado en Día Natural (00:00-23:59) vs Reportes Analíticos (23:00-23:00).

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    CRAZYTIME SYSTEM v3.0                    │
│                   Pure SQLite Architecture                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
          ┌───────────────────────────────────────┐
          │         main.py (Scheduler)           │
          │   Orquestador principal del sistema   │
          │      • Ciclos cada 5 minutos          │
          │      • Recuperación de brechas        │
          │      • 0% Dependencia de Disco        │
          └───────────────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            │                 │                 │
            ▼                 ▼                 ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │ DataCollector│  │PatternTracker│  │ AlertManager │
    │              │  │              │  │              │
    │ • API Client │  │ • Distancias │  │ • Umbrales   │
    │ • Escalera   │  │ • SQL States │  │ • Hits       │
    │ • Latidos    │  │ • Secuencias │  │ • Telegram   │
    └──────────────┘  └──────────────┘  └──────────────┘
            │                 │                 │
            └─────────────────┼─────────────────┘
                              ▼
                    ┌──────────────────┐
                    │   SQLite (WAL)   │
                    │  ┌────────────┐  │
                    │  │   tiros    │  │ ← Fuente de verdad (Datos)
                    │  │            │  │   • IDs inmutables
                    │  │            │  │   • Multiplicadores
                    │  ├────────────┤  │
                    │  │system_state│  │ ← Estado persistente (Memoria)
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
    │ • SQL Based  │  │ • HTML Rich  │  │ • FastAPI    │
    │ • ROI/WinRate│  │ • Retry Logic│  │ • SQL Live   │
    │ • Excel Rep. │  │ • Photo Supp.│  │ • Swagger UI │
    └──────────────┘  └──────────────┘  └──────────────┘
```

---

## 🔧 Requisitos

### Software Requerido
```bash
Python 3.11+
SQLite 3.35+ (Soporta UPSERT y Window Functions)
Git
```

---

## 📦 Instalación

```bash
git clone https://github.com/denisgemini/crazytime-public.git
cd crazytime-public
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
mkdir -p data/{logs,backups,analytics}
```

---

## 🚀 Uso

### Modo Servicio
```bash
python3 main.py
```

### Dashboard Web
```bash
python3 dashboard/app.py
```
Abre: **`http://localhost:8000`**

---

## 📁 Estructura del Proyecto

```
crazytime-public/
│
├── 📄 main.py                    # Punto de entrada principal
├── 📄 README.md                 # Este archivo
├── 📄 GEMINI.md                 # Instrucciones críticas
│
├── 📁 core/                     # Capa de datos y recolección
│   ├── database.py              # Motor SQLite (Fuente de verdad)
│   └── collector.py             # Recolector con escalera de recuperación
│
├── 📁 analytics/                # Módulos de inteligencia
│   ├── pattern_tracker.py       # Tracking de distancias en BD
│   ├── window_analyzer.py       # Auditoría ROI vía SQL
│   └── daily_report.py          # Reportes estratégicos
│
├── 📁 alerting/                 # Sistema de notificaciones
│   ├── alert_manager.py         # Lógica de umbrales independiente
│   └── notification.py          # Integración con Telegram
│
├── 📁 dashboard/                # Visualización
│   └── app.py                   # Servidor API REST (Pure SQLite)
│
└── 📁 data/                     # Datos persistentes
    ├── db.sqlite3               # Base de datos central (Datos + Estado)
    ├── 📁 logs/                 # Bitácora de eventos
    └── 📁 analytics/            # Reportes JSON/Excel generados
```

---

## 🧩 Módulos Principales (v3.0)

### `analytics/pattern_tracker.py`
**Responsabilidades:**
- Persistencia individual de patrones en `system_state`.
- Gestión de `prev_distance` para protección de alertas.
- Cálculo de distancias físicas entre IDs reales.

### `alerting/alert_manager.py`
**Responsabilidades:**
- Evaluación de umbrales de aviso prioritarios.
- Reporte de Hits a partir del inicio de zona de juego.
- Independencia total entre bloques de alerta.

### `dashboard/app.py`
**Responsabilidades:**
- Desacoplamiento total de archivos JSON.
- Cálculos estadísticos al vuelo mediante consultas SQL.
- Sincronización de estado LIVE con el servicio de fondo.

---

## 🗺️ Roadmap

### v3.0 (Estado Actual)
- [x] Migración completa a arquitectura Pure SQLite (Erradicación de JSONs legacy).
- [x] Dashboard centrado en impacto de pagos y multiplicadores.
- [x] Lógica de alertas blindada ante hits simultáneos.

### v3.1 (Próximamente)
- [ ] Implementación de Heatmaps de Flappers por franja horaria.
- [ ] Exportación de reportes de auditoría en PDF.
- [ ] Soporte multicanal para alertas VIP diferenciadas.

---

## 🤝 Contribución
Este proyecto es una herramienta de acumulación de ventaja estadística. Las contribuciones en algoritmos de análisis de varianza son bienvenidas.

---
*Este sistema está diseñado para transformar el azar en una serie de probabilidades explotables.*