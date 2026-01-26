"""
Dashboard Backend - FastAPI Server for CrazyTime v2 Dashboard
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

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from pydantic import BaseModel, Field

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# --------------------------------------------------
# FastAPI app
# --------------------------------------------------

app = FastAPI(
    title="CrazyTime v2 Dashboard API",
    description="REST API for CrazyTime v2 interactive dashboard",
    version="1.0.0"
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

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Base path configuration
BASE_DATA_PATH = PROJECT_ROOT / "data"
BASE_CONFIG_PATH = PROJECT_ROOT / "config"

# Database path
DB_PATH = BASE_DATA_PATH / "db.sqlite3"
TRACKER_STATE_PATH = BASE_DATA_PATH / ".tracker_state.json"
ALERT_STATE_PATH = BASE_DATA_PATH / ".alert_state.json"
DISTANCES_DIR = BASE_DATA_PATH / "distances"


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
    median_distance: Optional[int] = None
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


class AnalyticsWindow(BaseModel):
    pattern_id: str
    pattern_name: str
    threshold: int
    window_start_offset: int
    window_end_offset: int
    total_opportunities: int
    hits_in_window: int
    misses: int
    hit_rate: float
    roi: float


class AnalyticsResponse(BaseModel):
    windows: List[AnalyticsWindow]
    last_updated: str


class DailyStats(BaseModel):
    date: str
    total_spins: int
    results_distribution: Dict[str, int]


class SpinsStatsResponse(BaseModel):
    today_stats: DailyStats
    current_spin_id: int
    last_spin_time: Optional[str] = None


class GapRecord(BaseModel):
    timestamp: str
    duration_seconds: float
    gap_type: str
    details: str


class GapsResponse(BaseModel):
    gaps: List[GapRecord]
    count: int


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

@contextmanager
def get_db_connection(read_only: bool = True):
    """Get database connection with proper settings"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def get_tracker_state() -> dict:
    """Load tracker state from JSON file"""
    try:
        with open(TRACKER_STATE_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"last_processed_id": 0, "pattern_states": {}}


def get_alert_state() -> dict:
    """Load alert state from JSON file"""
    try:
        with open(ALERT_STATE_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def get_distances(pattern_id: str) -> dict:
    """Get distances data for a pattern"""
    filepath = DISTANCES_DIR / f"{pattern_id}.json"
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"distances": [], "statistics": {}}


def get_pattern_config() -> dict:
    """Get pattern definitions from config"""
    config_path = BASE_CONFIG_PATH / "patterns.py"
    try:
        with open(config_path, 'r') as f:
            content = f.read()
        patterns = {}
        for line in content.split('\n'):
            if '"pachinko"' in line or '"crazytime"' in line:
                patterns[line.split(':')[0].strip().strip('"')] = {
                    'name': line.split(':')[0].strip().strip('"').replace('_', ' ').title(),
                    'type': 'simple',
                    'value': line.split(':')[0].strip().strip('"'),
                    'thresholds': [50, 110] if 'pachinko' in line else [190, 250]
                }
        return patterns
    except FileNotFoundError:
        return {
            "pachinko": {"name": "Pachinko", "type": "simple", "value": "Pachinko", "thresholds": [50, 110]},
            "crazytime": {"name": "Crazy Time", "type": "simple", "value": "CrazyTime", "thresholds": [190, 250]}
        }


# ============== API Endpoints ==============

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serve the main dashboard HTML page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """Get overall system status"""
    with get_db_connection() as conn:
        last_spin = conn.execute(
            "SELECT id, resultado, timestamp FROM tiros ORDER BY id DESC LIMIT 1"
        ).fetchone()

        today = datetime.now().strftime("%Y-%m-%d")
        today_stats = conn.execute(
            "SELECT COUNT(*) as count FROM tiros WHERE timestamp LIKE ?",
            (f"{today}%",)
        ).fetchone()

        current_id = last_spin['id'] if last_spin else 0

        return StatusResponse(
            status="running" if current_id > 0 else "stopped",
            service_running=current_id > 0,
            last_spin_id=current_id,
            last_result=last_spin['resultado'] if last_spin else None,
            last_spin_time=last_spin['timestamp'] if last_spin else None,
            total_spins_today=today_stats['count'] if today_stats else 0,
            timestamp=datetime.now().isoformat()
        )


@app.get("/api/spins/recent", response_model=RecentSpinsResponse)
async def get_recent_spins(limit: int = Query(default=20, ge=1, le=100)):
    """Get recent spins"""
    with get_db_connection() as conn:
        spins = conn.execute(
            """SELECT id, resultado, timestamp, top_slot_result,
                      top_slot_multiplier, is_top_slot_matched, bonus_multiplier
               FROM tiros ORDER BY id DESC LIMIT ?""",
            (limit,)
        ).fetchall()

        return RecentSpinsResponse(
            spins=[SpinResult(**dict(row)) for row in spins],
            count=len(spins)
        )


@app.get("/api/spins/stats", response_model=SpinsStatsResponse)
async def get_spins_stats():
    """Get daily statistics"""
    with get_db_connection() as conn:
        today = datetime.now().strftime("%Y-%m-%d")

        today_stats = conn.execute(
            """SELECT resultado, COUNT(*) as count
               FROM tiros WHERE timestamp LIKE ?
               GROUP BY resultado""",
            (f"{today}%",)
        ).fetchall()

        distribution = {row['resultado']: row['count'] for row in today_stats}

        last_spin = conn.execute(
            "SELECT id, timestamp FROM tiros ORDER BY id DESC LIMIT 1"
        ).fetchone()

        return SpinsStatsResponse(
            today_stats=DailyStats(
                date=today,
                total_spins=sum(distribution.values()),
                results_distribution=distribution
            ),
            current_spin_id=last_spin['id'] if last_spin else 0,
            last_spin_time=last_spin['timestamp'] if last_spin else None
        )


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


@app.get("/api/alerts", response_model=AlertsResponse)
async def get_alerts():
    """Get current alert status"""
    alert_state = get_alert_state()
    tracker_state = get_tracker_state()
    pattern_config = get_pattern_config()

    current_id = tracker_state.get("last_processed_id", 0)

    alerts = []
    active_count = 0

    for pattern_id, config in pattern_config.items():
        pattern_alerts = alert_state.get(pattern_id, {})
        thresholds = config.get("thresholds", [])

        for threshold in thresholds:
            thresh_data = pattern_alerts.get("thresholds", {}).get(str(threshold), {})
            status = thresh_data.get("status", "idle")

            if status in ["approaching", "ready"]:
                active_count += 1

            last_seen_id = tracker_state.get("pattern_states", {}).get(pattern_id, {}).get("last_id", 0)
            current_wait = current_id - last_seen_id

            alerts.append(AlertStatus(
                pattern_id=pattern_id,
                pattern_name=config.get("name", pattern_id.title()),
                threshold=threshold,
                current_wait=current_wait,
                status=status,
                last_alert_time=thresh_data.get("last_alert_time")
            ))

    return AlertsResponse(
        alerts=alerts,
        active_count=active_count
    )


@app.get("/api/analytics/window", response_model=AnalyticsResponse)
async def get_analytics_window():
    """Get window analysis for VIP patterns"""
    analytics_dir = BASE_DATA_PATH / "analytics"
    pattern_config = get_pattern_config()

    windows = []

    for pattern_id in pattern_config.keys():
        filepath = analytics_dir / f"{pattern_id}_window_analysis.json"
        if filepath.exists():
            with open(filepath, 'r') as f:
                data = json.load(f)
                for result in data.get("results", []):
                    windows.append(AnalyticsWindow(
                        pattern_id=pattern_id,
                        pattern_name=pattern_config[pattern_id].get("name", pattern_id.title()),
                        threshold=result.get("threshold", 0),
                        window_start_offset=result.get("window_start_offset", 0),
                        window_end_offset=result.get("window_end_offset", 0),
                        total_opportunities=result.get("total_opportunities", 0),
                        hits_in_window=result.get("hits_in_window", 0),
                        misses=result.get("misses", 0),
                        hit_rate=result.get("hit_rate", 0),
                        roi=result.get("roi", 0)
                    ))

    return AnalyticsResponse(
        windows=windows,
        last_updated=datetime.now().isoformat()
    )


@app.get("/api/gaps", response_model=GapsResponse)
async def get_gaps(limit: int = Query(default=20, ge=1, le=100)):
    """Get service gap records"""
    gaps_file = BASE_DATA_PATH / "bitacora_brechas.csv"
    gaps = []

    if not gaps_file.exists():
        return GapsResponse(gaps=[], count=0)

    try:
        with open(gaps_file, 'r') as f:
            lines = f.readlines()
            for line in lines[-limit:]:
                parts = line.strip().split(',')
                if len(parts) < 4:
                    continue  # Skip malformed lines
                try:
                    gaps.append(GapRecord(
                        timestamp=parts[0],
                        duration_seconds=float(parts[1]),
                        gap_type=parts[2],
                        details=",".join(parts[3:])
                    ))
                except (ValueError, IndexError):
                    continue  # Skip lines with conversion errors
    except FileNotFoundError:
        return GapsResponse(gaps=[], count=0)
    except Exception as e:
        # Log the error for debugging
        logging.error(f"Error reading gaps file: {e}")
        raise HTTPException(status_code=500, detail="Error processing gaps data")

    return GapsResponse(
        gaps=gaps[::-1],
        count=len(gaps)
    )


@app.get("/api/patterns", response_model=PatternsResponse)
async def get_patterns():
    tracker_state = get_tracker_state()
    alert_state = get_alert_state()
    pattern_config = get_pattern_config()

    current_id = tracker_state.get("last_processed_id", 0)
    last_result = tracker_state.get("last_result")

    patterns = []
    for pattern_id, config in pattern_config.items():
        pattern_state = tracker_state.get("pattern_states", {}).get(pattern_id, {})
        alert_data = alert_state.get(pattern_id, {})
        
        last_seen_id = pattern_state.get("last_id")
        
        if last_seen_id is None or last_seen_id == 0:
            last_seen_id = alert_data.get("last_seen_id", 0)
        
        if last_seen_id and last_seen_id > 0:
            spins_since = current_id - last_seen_id
        else:
            spins_since = current_id

        thresholds_status = {}
        thresholds = config.get("thresholds", [])
        for threshold in thresholds:
            alert_thresh = alert_data.get("thresholds", {}).get(str(threshold), {})
            thresholds_status[str(threshold)] = {
                "status": alert_thresh.get("status", "idle"),
                "last_alert_time": alert_thresh.get("last_alert_time"),
                "progress": min(100, int(spins_since / threshold * 100)) if threshold > 0 else 0
            }

        patterns.append(PatternStatus(
            pattern_id=pattern_id,
            pattern_name=config.get("name", pattern_id.title()),
            type=config.get("type", "simple"),
            value=config.get("value", pattern_id),
            last_spin_id=last_seen_id if last_seen_id and last_seen_id > 0 else None,
            last_result=last_result,
            spins_since=spins_since,
            current_distance=spins_since,
            thresholds=thresholds,
            thresholds_status=thresholds_status
        ))

    return PatternsResponse(
        patterns=patterns,
        last_updated=datetime.now().isoformat()
    )


# ============== Main Entry Point ==============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
