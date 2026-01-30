"""
Dashboard Backend - FastAPI Server for CrazyTime v3.0 (Pure SQLite)
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json
import sqlite3
import logging
import statistics

# --- Configuración de Rutas de Sistema ---
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

BASE_DATA_PATH = ROOT_DIR / "data"
DB_PATH = BASE_DATA_PATH / "db.sqlite3"

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from pydantic import BaseModel

from core.database import Database
from config.patterns import ALL_PATTERNS, VIP_PATTERNS, TRACKING_PATTERNS

# Inicializar BD
db = Database(str(DB_PATH))

app = FastAPI(title="CrazyTime v3.0 Dashboard", version="3.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# ============== Models ============== 

class SpinResult(BaseModel):
    id: int
    resultado: str
    timestamp: str

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
    spins_since: int
    current_distance: int
    last_distance: Optional[int]
    thresholds: List[int]

class PatternsResponse(BaseModel):
    patterns: List[PatternStatus]
    last_updated: str

class AlertStatus(BaseModel):
    pattern_id: str
    pattern_name: str
    threshold: int
    current_wait: int
    status: str

class AlertsResponse(BaseModel):
    alerts: List[AlertStatus]
    active_count: int

class StatusResponse(BaseModel):
    status: str
    last_spin_id: int
    last_result: Optional[str]
    total_spins_today: int
    timestamp: str

# ============== Helpers ============== 

def calculate_distances_from_db(pattern_value: str, limit: int = 50):
    """Calcula distancias e historial directamente desde la tabla tiros"""
    with db.get_connection(read_only=True) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM tiros WHERE resultado = ? ORDER BY id DESC LIMIT ?", (pattern_value, limit + 1))
        ids = [row[0] for row in cur.fetchall()]
        
        if len(ids) < 2:
            return [], {}
            
        # Las IDs vienen de nueva a vieja, invertimos para calcular saltos cronológicos
        ids.reverse()
        distances = [ids[i+1] - ids[i] for i in range(len(ids)-1)]
        
        stats = {
            "count": len(distances),
            "mean": round(statistics.mean(distances), 1) if distances else 0,
            "median": int(statistics.median(distances)) if distances else 0,
            "min": min(distances) if distances else 0,
            "max": max(distances) if distances else 0
        }
        return distances, stats

# ============== API Endpoints ============== 

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    last_spin = db.get_last_spin()
    stats_dia = db.obtener_estadisticas_dia()
    return StatusResponse(
        status="active" if last_spin else "idle",
        last_spin_id=last_spin['id'] if last_spin else 0,
        last_result=last_spin['resultado'] if last_spin else None,
        total_spins_today=stats_dia.get('total_spins', 0),
        timestamp=datetime.now().isoformat()
    )

@app.get("/api/patterns", response_model=PatternsResponse)
async def get_patterns():
    current_max_id = db.get_max_id() or 0
    patterns = []
    
    for p in VIP_PATTERNS + TRACKING_PATTERNS:
        # Obtener estado oficial desde system_state
        p_state = db.get_state("pattern_tracker", p.id, {"last_id": None, "last_distance": 0})
        last_id = p_state.get("last_id")
        
        spins_since = current_max_id - last_id if last_id else 0
        
        patterns.append(PatternStatus(
            pattern_id=p.id,
            pattern_name=p.name,
            spins_since=spins_since,
            current_distance=spins_since,
            last_distance=p_state.get("last_distance"),
            thresholds=p.warning_thresholds
        ))
    return PatternsResponse(patterns=patterns, last_updated=datetime.now().isoformat())

@app.get("/api/alerts", response_model=AlertsResponse)
async def get_alerts():
    current_max_id = db.get_max_id() or 0
    manager_state = db.get_state("alert_manager", "main_state", {})
    alerts = []
    active_count = 0
    
    for p in VIP_PATTERNS:
        p_tracker = db.get_state("pattern_tracker", p.id, {"last_id": None})
        last_id = p_tracker.get("last_id")
        if not last_id: continue
        
        current_wait = current_max_id - last_id
        p_alerts = manager_state.get(p.id, {}).get("alerts_sent", {})
        
        for threshold in p.warning_thresholds:
            is_sent = p_alerts.get(str(threshold), False)
            if is_sent:
                active_count += 1
                alerts.append(AlertStatus(
                    pattern_id=p.id, pattern_name=p.name,
                    threshold=threshold, current_wait=current_wait,
                    status="triggered"
                ))
    return AlertsResponse(alerts=alerts, active_count=active_count)

@app.get("/api/patterns/{pattern_id}/distances", response_model=PatternDistancesResponse)
async def get_pattern_distances(pattern_id: str, limit: int = Query(default=50, ge=1, le=200)):
    p_config = next((p for p in ALL_PATTERNS if p.id == pattern_id), None)
    if not p_config:
        raise HTTPException(status_code=404, detail="Pattern not found")
        
    distances, stats = calculate_distances_from_db(p_config.value, limit)
    
    return PatternDistancesResponse(
        pattern_id=pattern_id,
        pattern_name=p_config.name,
        distances=distances,
        statistics=PatternStats(
            pattern_id=pattern_id, pattern_name=p_config.name,
            count=stats.get("count", 0),
            mean_distance=stats.get("mean"),
            median_distance=stats.get("median"),
            min_distance=stats.get("min"),
            max_distance=stats.get("max")
        )
    )

@app.get("/api/spins/recent", response_model=RecentSpinsResponse)
async def get_recent_spins(limit: int = Query(default=20, ge=1, le=100)):
    spins = db.get_spins_after_id(db.get_max_id() - limit if db.get_max_id() else 0)
    return RecentSpinsResponse(
        spins=[SpinResult(id=s['id'], resultado=r['resultado'], timestamp=s['timestamp']) 
               for s in reversed(spins)], # Recientes arriba
        count=len(spins)
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
