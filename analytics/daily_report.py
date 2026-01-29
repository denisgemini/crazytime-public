"""
analytics/daily_report.py - Generador de reportes diarios estratégicos.
Enfoque: Análisis puro de VENTANAS DE APUESTA (Wins/Losses).
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List

from core.database import Database
from config.patterns import VIP_PATTERNS, TRACKING_PATTERNS, get_window_range

logger = logging.getLogger(__name__)

class DailyReportGenerator:
    """Genera el reporte diario centrado en la rentabilidad de las ventanas."""

    def __init__(self, db_path: str = "data/db.sqlite3"):
        self.db = Database(db_path)
        self.distances_dir = "data/distances"

    def generate(self) -> Optional[Dict]:
        """Genera el reporte completo del día (cierre 23:00-23:00)."""
        try:
            # 1. Obtener estadísticas base de BD
            db_stats = self.db.obtener_estadisticas_dia()
            if db_stats.get("total_spins", 0) == 0:
                return None

            start_iso = db_stats["range_start"]
            end_iso = db_stats["range_end"]

            # 2. Procesar Patrones
            patterns_report = []
            all_patterns = VIP_PATTERNS + TRACKING_PATTERNS
            
            for pattern in all_patterns:
                p_data = self._analyze_pattern_windows(pattern, start_iso, end_iso)
                if p_data:
                    patterns_report.append(p_data)

            # 3. Estructura final
            return {
                "total_spins": db_stats["total_spins"],
                "range_start": start_iso,
                "range_end": end_iso,
                "patterns": patterns_report,
                "latidos": db_stats["latidos"]
            }

        except Exception as e:
            logger.error(f"Error generando reporte diario: {e}", exc_info=True)
            return None

    def _analyze_pattern_windows(self, pattern, start_iso, end_iso) -> Optional[Dict]:
        """Calcula Wins/Losses para las ventanas de apuesta definidas."""
        filepath = os.path.join(self.distances_dir, f"{pattern.id}.json")
        if not os.path.exists(filepath):
            return None

        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            
            all_occurrences = data.get("occurrences", [])
            
            # Conteo de apariciones totales en el día
            day_count = len([
                occ for occ in all_occurrences 
                if start_iso <= occ["timestamp"] < end_iso
            ])

            if day_count == 0:
                return {
                    "id": pattern.id,
                    "name": pattern.name,
                    "count": 0,
                    "windows": []
                }

            # Análisis centrado en VENTANAS
            window_stats = []
            
            # Aunque la config usa 'thresholds' para definir ventanas,
            # aquí abstraemos eso y hablamos de 'window_zones'.
            for threshold_def in pattern.thresholds:
                w_start, w_end = get_window_range(threshold_def)
                
                entries = 0  # Veces que entramos a la zona de apuesta
                wins = 0     # Veces que ganamos DENTRO de la zona
                losses = 0   # Veces que perdimos (salimos de la zona sin ganar)

                for i in range(len(all_occurrences) - 1):
                    curr = all_occurrences[i]
                    
                    # Filtro de fecha: Solo oportunidades nacidas HOY
                    if not (start_iso <= curr["timestamp"] < end_iso):
                        continue
                    
                    next_occ = all_occurrences[i+1]
                    dist = next_occ.get("distance_from_previous")
                    
                    if dist is None:
                        continue

                    # LÓGICA DE NEGOCIO: ZONA DE APUESTA
                    # 1. ¿Llegamos a la zona de apuesta?
                    if dist < w_start:
                        continue # No se entró. No cuenta.
                    
                    # Si llegamos aquí, ENTRAMOS a la ventana.
                    entries += 1
                    
                    # 2. Evaluación de Resultado (Win vs Loss)
                    target_start = curr["spin_id"] + w_start
                    target_end = curr["spin_id"] + w_end
                    real_next_id = next_occ["spin_id"]

                    if target_start <= real_next_id <= target_end:
                        wins += 1
                    else:
                        # Si entramos (dist >= w_start) y no fue win, entonces fue loss (> w_end)
                        losses += 1
                
                window_stats.append({
                    "window_range": f"[{w_start}-{w_end}]", # Identificador puramente de ventana
                    "entries": entries,
                    "wins": wins,
                    "losses": losses,
                    # Mantener compatibilidad con el template de notificación (temporalmente)
                    "threshold": threshold_def, 
                    "hits": wins,
                    "misses": losses
                })

            return {
                "id": pattern.id,
                "name": pattern.name,
                "count": day_count,
                "windows": window_stats
            }

        except Exception as e:
            logger.error(f"Error analizando ventanas para {pattern.id}: {e}")
            return None