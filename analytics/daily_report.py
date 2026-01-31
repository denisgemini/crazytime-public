"""
analytics/daily_report.py - Reportes diarios estratégicos desde SQLite (v3.0).
"""

import logging
from datetime import datetime
from typing import Optional, Dict, List

from core.database import Database
from config.patterns import VIP_PATTERNS, TRACKING_PATTERNS, get_window_range

logger = logging.getLogger(__name__)

class DailyReportGenerator:
    """Genera el reporte diario centrado en rentabilidad usando exclusivamente la BD."""

    def __init__(self, db_path: str = "data/db.sqlite3"):
        self.db = Database(db_path)

    def generate(self) -> Optional[Dict]:
        """Genera el reporte completo del día (cierre estratégico 23:00-23:00)."""
        try:
            # Lógica "Cierre de Jornada": 23:00 ayer a 23:00 hoy
            now = datetime.now()
            today_23 = now.replace(hour=23, minute=0, second=0, microsecond=0)
            yesterday_23 = today_23 - timedelta(days=1)
            
            start_iso = yesterday_23.isoformat()
            end_iso = today_23.isoformat()

            db_stats = self.db.obtener_estadisticas_rango(start_iso, end_iso)
            if db_stats.get("total_spins", 0) == 0:
                return None

            patterns_report = []
            all_patterns = VIP_PATTERNS + TRACKING_PATTERNS
            
            for pattern in all_patterns:
                p_data = self._analyze_pattern_in_db(pattern, start_iso, end_iso)
                if p_data:
                    patterns_report.append(p_data)

            return {
                "total_spins": db_stats["total_spins"],
                "range_start": start_iso,
                "range_end": end_iso,
                "patterns": patterns_report,
                "latidos": db_stats["latidos"]
            }
        except Exception as e:
            logger.error(f"Error generando reporte diario: {e}")
            return None

    def _analyze_pattern_in_db(self, pattern, start_iso, end_iso) -> Optional[Dict]:
        """Analiza ventanas de un patrón consultando la tabla tiros."""
        try:
            with self.db.get_connection(read_only=True) as conn:
                cur = conn.cursor()
                # Obtenemos los tiros del patrón hasta el fin del día
                cur.execute("""
                    SELECT id, timestamp FROM tiros 
                    WHERE resultado = ? AND timestamp < ?
                    ORDER BY id ASC
                """, (pattern.value, end_iso))
                
                rows = cur.fetchall()
                if not rows:
                    return {"id": pattern.id, "name": pattern.name, "count": 0, "windows": []}

                # Convertir a lista de dicts
                occs = [dict(r) for r in rows]
                
                # Filtrar conteo de apariciones del día real
                day_count = len([o for o in occs if o["timestamp"] >= start_iso])

                window_stats = []
                # Usamos los thresholds definidos en config/patterns.py
                thresholds = pattern.warning_thresholds
                
                for t_def in thresholds:
                    w_start, w_end = get_window_range(t_def)
                    hits, misses = 0, 0

                    for i in range(len(occs) - 1):
                        # La oportunidad nace en occs[i]
                        # Solo analizamos si el tiro base ocurrió dentro de la jornada
                        if not (start_iso <= occs[i]["timestamp"] < end_iso):
                            continue
                        
                        # Distancia al siguiente tiro del mismo patrón
                        dist = occs[i+1]["id"] - occs[i]["id"]
                        
                        # Si la distancia es >= inicio de ventana, entramos a jugar
                        if dist >= w_start:
                            if dist <= w_end:
                                hits += 1
                            else:
                                misses += 1
                    
                    window_stats.append({
                        "window_range": f"[{w_start}-{w_end}]",
                        "hits": hits,
                        "misses": misses
                    })

                return {
                    "id": pattern.id,
                    "name": pattern.name,
                    "count": day_count,
                    "windows": window_stats
                }
        except Exception as e:
            logger.error(f"Error analizando {pattern.id} en DB: {e}")
            return None
