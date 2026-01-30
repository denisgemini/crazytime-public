"""
alerting/alert_manager.py - Gestión de alertas con lógica de distancia previa (v3.1).
"""

import logging
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

from config.patterns import Pattern, VIP_PATTERNS
from core.database import Database

logger = logging.getLogger(__name__)

class AlertType(Enum):
    THRESHOLD_REACHED = "threshold_reached" # Aviso
    PATTERN_HIT = "pattern_hit"             # Salida en zona

@dataclass
class Alert:
    type: AlertType
    pattern_id: str
    pattern_name: str
    value: int | str 
    spin_count: int 
    timestamp: datetime
    details: dict

class AlertManager:
    """Gestor de alertas basado en SQLite con soporte para HIT simultáneo."""

    def __init__(self, db_path: str = "data/db.sqlite3"):
        self.db = Database(db_path)
        self.state = self._load_state()

    def _load_state(self) -> dict:
        """Carga la memoria de alertas enviadas."""
        return self.db.get_state("alert_manager", "main_state", {})

    def _save_state(self):
        """Guarda la memoria de alertas enviadas."""
        self.db.set_state("alert_manager", "main_state", self.state)

    def check_all_patterns(self) -> list[Alert]:
        all_alerts = []
        current_max_id = self.db.get_max_id()
        if not current_max_id:
            return []

        for pattern in VIP_PATTERNS:
            # Leer fuente de verdad del Tracker en SQLite
            p_tracker_data = self.db.get_state("pattern_tracker", pattern.id, 
                                              {"last_id": None, "last_distance": 0, "prev_distance": 0})
            
            if p_tracker_data["last_id"]:
                alerts = self.check_pattern(pattern, current_max_id, p_tracker_data)
                all_alerts.extend(alerts)
        
        self._save_state()
        return all_alerts

    def check_pattern(self, pattern: Pattern, current_max_id: int, tracker_data: dict) -> list[Alert]:
        alerts = []
        tracker_last_id = tracker_data.get("last_id")
        last_distance = tracker_data.get("last_distance", 0)
        prev_distance = tracker_data.get("prev_distance", 0)

        p_state = self.state.setdefault(pattern.id, {
            "last_processed_id": tracker_last_id,
            "alerts_sent": {}
        })

        # Regla de Oro: Detectar si hubo hit en este ciclo
        is_hit = tracker_last_id > p_state["last_processed_id"]

        # Determinar el ID donde comenzó esta racha para calcular el ID exacto de cada umbral
        if is_hit:
            distance_for_thresholds = prev_distance
            start_id = tracker_last_id - prev_distance
        else:
            distance_for_thresholds = last_distance
            start_id = tracker_last_id

        # =================================================================
        # BLOQUE 1: UMBRALES (Avisos de calor)
        # =================================================================
        for threshold in pattern.warning_thresholds:
            t_key = str(threshold)
            if distance_for_thresholds >= threshold and not p_state["alerts_sent"].get(t_key):
                # Calcular el ID del tiro que cruzó el umbral y buscar su hora real
                threshold_spin_id = start_id + threshold
                alert_time = datetime.now()
                spin_data = self.db.get_spin_by_id(threshold_spin_id)
                if spin_data and spin_data.get("timestamp"):
                    try:
                        alert_time = datetime.fromisoformat(spin_data["timestamp"])
                    except: pass

                alerts.append(Alert(
                    type=AlertType.THRESHOLD_REACHED,
                    pattern_id=pattern.id,
                    pattern_name=pattern.name,
                    value=threshold,
                    spin_count=distance_for_thresholds,
                    timestamp=alert_time,
                    details={}
                ))
                logger.info(f"🔔 [{pattern.name}] AVISO UMBRAL {threshold} (Dist: {distance_for_thresholds})")
                p_state["alerts_sent"][t_key] = True

        # =================================================================
        # BLOQUE 2: HITS (Reporte de salida)
        # =================================================================
        if is_hit:
            # Usamos prev_distance para el reporte del HIT ya que es la distancia real recorrida
            if prev_distance > 0 and pattern.betting_windows:
                start_game_zone = pattern.betting_windows[0][0]
                if prev_distance >= start_game_zone:
                    details = self._get_hit_details(pattern, tracker_last_id)
                    
                    # Obtener hora real del hit desde los detalles
                    hit_time = datetime.now()
                    if details.get("timestamp"):
                        try:
                            hit_time = datetime.fromisoformat(details["timestamp"])
                        except: pass

                    alerts.append(Alert(
                        type=AlertType.PATTERN_HIT,
                        pattern_id=pattern.id,
                        pattern_name=pattern.name,
                        value=prev_distance,
                        spin_count=prev_distance,
                        timestamp=hit_time,
                        details=details
                    ))
                    logger.info(f"🎉 [{pattern.name}] SALIDA DETECTADA (Distancia: {prev_distance})")

            # Reseteo total tras el hit
            p_state["alerts_sent"] = {} 
            p_state["last_processed_id"] = tracker_last_id

        return alerts

    def _get_hit_details(self, pattern: Pattern, spin_id: int) -> dict:
        spin_data = self.db.get_spin_by_id(spin_id)
        if not spin_data:
            return {}
        details = {
            "resultado": spin_data["resultado"],
            "timestamp": spin_data["timestamp"]
        }
        if pattern.id == "pachinko":
            details["bonus_multiplier"] = spin_data.get("bonus_multiplier")
            details["top_slot_matched"] = spin_data.get("is_top_slot_matched", False)
            details["top_slot_multiplier"] = spin_data.get("top_slot_multiplier")
        elif pattern.id == "crazytime":
            details["flapper_blue"] = spin_data.get("ct_flapper_blue")
            details["flapper_green"] = spin_data.get("ct_flapper_green")
            details["flapper_yellow"] = spin_data.get("ct_flapper_yellow")
            details["top_slot_matched"] = spin_data.get("is_top_slot_matched", False)
            details["top_slot_multiplier"] = spin_data.get("top_slot_multiplier")
        return details