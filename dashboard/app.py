"""
Dashboard Backend - FastAPI Server for CrazyTime v2.5 Dashboard (CLEAN)
Provides REST API endpoints for the interactive dashboard
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
import json
import sqlite3
import logging

# --- Configuración de Logging para Diagnóstico ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("dashboard_init")
logger.info("🚀 Iniciando proceso de arranque del Dashboard v2.5...")

# --- Configuración de Rutas de Sistema (Debe ir antes de las importaciones locales) ---
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

logger.info(f"📂 ROOT_DIR configurado en: {ROOT_DIR}")

# Configuración de rutas de datos
BASE_DATA_PATH = ROOT_DIR / "data"
BASE_CONFIG_PATH = ROOT_DIR / "config"
DB_PATH = BASE_DATA_PATH / "db.sqlite3"
DISTANCES_DIR = BASE_DATA_PATH / "distances"

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from pydantic import BaseModel, Field

# Importaciones locales de CrazyTime (ahora que el path está configurado)
logger.info("📦 Cargando módulos core y config...")
from core.database import Database
from config.patterns import ALL_PATTERNS

# Inicializar manejador de base de datos global
logger.info(f"🗄️ Inicializando conexión a base de datos en: {DB_PATH}")
db = Database(str(DB_PATH))
logger.info("✅ Base de datos inicializada correctamente")

# --------------------------------------------------
# FastAPI app
# --------------------------------------------------

app = FastAPI(
    title="CrazyTime v2.5 Dashboard API",
    description="REST API for CrazyTime v2.5 interactive dashboard",
    version="2.5.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files (CSS / JS)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Templates
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# ============== Pydantic Models ============== 

class SpinResult(BaseModel):
    id: int
    resultado: str
    timestamp: str
    top_slot_result: Optional[str] = None
    top_slot_multiplier: Optional[int] = None
    is_top_slot_matched: Optional[bool] = None
    bonus_multiplier: Optional[int] = None

class RecentSpinsResponse(BaseModel):
    spins: List[SpinResult]
    count: int

class PatternStats(BaseModel):
    pattern_id: str
    pattern_name: str
    count: int
    mean_distance: Optional[float] = None
    median_distance: Optional[float] = None
    min_distance: Optional[int] = None
    max_distance: Optional[int] = None

class PatternDistancesResponse(BaseModel):
    pattern_id: str
    pattern_name: str
    distances: List[int]
    statistics: PatternStats

class PatternStatus(BaseModel):
    pattern_id: str
    pattern_name: str
    type: str
    value: str
    last_spin_id: Optional[int] = None
    last_result: Optional[str] = None
    spins_since: int = 0
    current_distance: int
    thresholds: List[int]
    thresholds_status: Dict[str, Dict[str, Any]]

class PatternsResponse(BaseModel):
    patterns: List[PatternStatus]
    last_updated: str

class AlertStatus(BaseModel):
    pattern_id: str
    pattern_name: str
    threshold: int
    current_wait: int
    status: str
    last_alert_time: Optional[str] = None

class AlertsResponse(BaseModel):
    alerts: List[AlertStatus]
    active_count: int

class StatusResponse(BaseModel):
    status: str
    service_running: bool
    last_spin_id: int
    last_result: Optional[str] = None
    last_spin_time: Optional[str] = None
    total_spins_today: int
    uptime_seconds: Optional[int] = None
    timestamp: str

# ============== Database Helpers ============== 

def get_db_connection():
    """Usa la clase Database global para obtener una conexión optimizada"""
    return db.get_connection(read_only=True)

def get_tracker_state() -> dict:
    """Obtiene el estado del tracker desde la BD (v2.6)"""
    state = db.get_state("pattern_tracker", "main_state")
    if not state:
        return {"last_processed_id": 0, "pattern_states": {}}
    return state

def get_alert_state() -> dict:
    """Obtiene el estado de alertas desde la BD (v2.6)"""
    state = db.get_state("alert_manager", "main_state")
    if not state:
        return {}
    return state

def get_distances(pattern_id: str) -> dict:
    filepath = DISTANCES_DIR / f"{pattern_id}.json"
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"distances": [], "statistics": {}}

# ============== Configuration Cache ============== 

# Cargar configuración una sola vez al inicio
def _init_pattern_config():
    patterns = {}
    for p in ALL_PATTERNS:
        # Solo nos interesan Pachinko y CrazyTime para el dashboard principal por ahora
        if p.id in ['pachinko', 'crazytime']:
            patterns[p.id] = {
                'name': p.name,
                'type': p.type,
                'value': p.value,
                'thresholds': p.thresholds
            }
    return patterns

PATTERN_CONFIG_CACHE = _init_pattern_config()

def get_pattern_config() -> dict:
    """Retorna la configuración desde la caché para máxima eficiencia"""
    return PATTERN_CONFIG_CACHE

# ============== API Endpoints ============== 

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    print("➡️ Solicitud recibida: /api/status")
    try:
        # Obtener estadísticas del día usando el método oficial
        stats_dia = db.obtener_estadisticas_dia()
        
        # Obtener último tiro real
        last_spin = db.get_last_spin()
        
        current_id = last_spin['id'] if last_spin else 0
        print(f"   Current ID: {current_id}")

        return StatusResponse(
            status="running" if current_id > 0 else "stopped",
            service_running=current_id > 0,
            last_spin_id=current_id,
            last_result=last_spin['resultado'] if last_spin else None,
            last_spin_time=last_spin['timestamp'] if last_spin else None,
            total_spins_today=stats_dia.get('total_spins', 0),
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        print(f"❌ ERROR en get_status: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/patterns", response_model=PatternsResponse)
async def get_patterns():
    tracker_state = get_tracker_state()
    pattern_config = get_pattern_config()
    current_id = tracker_state.get("last_processed_id", 0)
    patterns = []
    for p_id, config in pattern_config.items():
        p_state = tracker_state.get("pattern_states", {}).get(p_id, {})
        last_seen_id = p_state.get("last_id")
        spins_since = current_id - last_seen_id if last_seen_id is not None else current_id
        patterns.append(PatternStatus(
            pattern_id=p_id, pattern_name=config.get("name", p_id),
            type=config.get("type", "simple"), value=config.get("value", p_id),
            spins_since=spins_since, current_distance=spins_since,
            thresholds=config.get("thresholds", []),
            thresholds_status={}
        ))
    return PatternsResponse(patterns=patterns, last_updated=datetime.now().isoformat())

@app.get("/api/alerts", response_model=AlertsResponse)
async def get_alerts():
    alert_state = get_alert_state()
    tracker_state = get_tracker_state()
    pattern_config = get_pattern_config()
    current_id = tracker_state.get("last_processed_id", 0)
    alerts = []
    active_count = 0
    for p_id, config in pattern_config.items():
        p_alerts = alert_state.get(p_id, {})
        for threshold in config.get("thresholds", []):
            thresh_data = p_alerts.get("thresholds", {}).get(str(threshold), {})
            status = thresh_data.get("status", "idle")
            if status in ["approaching", "ready"]:
                active_count += 1
            last_seen_id = tracker_state.get("pattern_states", {}).get(p_id, {}).get("last_id", 0)
            alerts.append(AlertStatus(
                pattern_id=p_id, pattern_name=config.get("name", p_id),
                threshold=threshold, current_wait=current_id - last_seen_id,
                status=status, last_alert_time=thresh_data.get("last_alert_time")
            ))
    return AlertsResponse(alerts=alerts, active_count=active_count)

@app.get("/api/spins/recent", response_model=RecentSpinsResponse)
async def get_recent_spins(limit: int = Query(default=20, ge=1, le=100)):
    with get_db_connection() as conn:
        spins = conn.execute(
            "SELECT id, resultado, timestamp FROM tiros ORDER BY id DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return RecentSpinsResponse(
            spins=[SpinResult(id=r['id'], resultado=r['resultado'], timestamp=r['timestamp']) for r in spins],
            count=len(spins)
        )

@app.get("/api/spins/stats")
async def get_spins_stats():
    """Get statistics for the last 1000 spins using WAL for safety"""
    with get_db_connection() as conn:
        # Distribución de los últimos 1000 tiros
        stats_query = conn.execute(
            """SELECT resultado, COUNT(*) as count
               FROM (SELECT resultado FROM tiros ORDER BY id DESC LIMIT 1000)
               GROUP BY resultado"""
        ).fetchall()

        distribution = {row['resultado']: row['count'] for row in stats_query}

        # Incluir conteos de secuencias desde archivos JSON
        for seq_id in ['seq_5_2', 'seq_2_5']:
            try:
                seq_data = get_distances(seq_id)
                count = seq_data.get("statistics", {}).get("count", 0)
                # Usar el nombre corto para el gráfico
                label = "5-2" if seq_id == "seq_5_2" else "2-5"
                distribution[label] = count
            except Exception:
                continue

        last_spin = conn.execute(
            "SELECT id, timestamp FROM tiros ORDER BY id DESC LIMIT 1"
        ).fetchone()

        # Conteo de hoy para el header
        today = datetime.now().strftime("%Y-%m-%d")
        today_count = conn.execute(
            "SELECT COUNT(*) as count FROM tiros WHERE timestamp LIKE ?",
            (f"{today}%",)
        ).fetchone()

        return {
            "today_stats": {
                "date": today,
                "total_spins": today_count['count'] if today_count else 0,
                "results_distribution": distribution
            },
            "current_spin_id": last_spin['id'] if last_spin else 0,
            "last_spin_time": last_spin['timestamp'] if last_spin else None
        }

@app.get("/api/patterns/{pattern_id}/distances", response_model=PatternDistancesResponse)
async def get_pattern_distances(pattern_id: str, limit: int = Query(default=50, ge=1, le=200)):
    """Get distance history and statistics for a pattern"""
    distances_data = get_distances(pattern_id)
    pattern_config = get_pattern_config()

    distances = distances_data.get("distances", [])[-limit:]
    stats = distances_data.get("statistics", {})

    return PatternDistancesResponse(
        pattern_id=pattern_id,
        pattern_name=pattern_config.get(pattern_id, {}).get("name", pattern_id.title()),
        distances=distances,
        statistics=PatternStats(
            pattern_id=pattern_id,
            pattern_name=pattern_config.get(pattern_id, {}).get("name", pattern_id.title()),
            count=stats.get("count", len(distances)),
            mean_distance=stats.get("mean"),
            median_distance=stats.get("median"),
            min_distance=stats.get("min") if distances else None,
            max_distance=stats.get("max") if distances else None
        )
    )


@app.get("/{path:path}", response_class=HTMLResponse)
async def spa_fallback(request: Request, path: str):
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)