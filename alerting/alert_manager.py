"""
alerting/alert_manager.py - Gestión de alertas INDEPENDIENTES.
Se sincroniza con PatternTracker para obtener distancias oficiales.
"""

import os
import json
import logging
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from config.patterns import Pattern, VIP_PATTERNS, get_window_range
from core.database import Database

logger = logging.getLogger(__name__)

class AlertType(Enum):
    THRESHOLD_REACHED = "threshold_reached"
    PATTERN_HIT = "pattern_hit"

@dataclass
class Alert:
    type: AlertType
    pattern_id: str
    pattern_name: str
    threshold: int
    spin_count: int 
    timestamp: datetime
    details: dict

class AlertManager:
    """Gestor de alertas alineado con PatternTracker."""

    def __init__(self, db_path: str = "data/db.sqlite3"):
        self.db = Database(db_path)
        self.distances_dir = "data/distances"
        self.state = self._load_state()

    def _load_state(self) -> dict:
        state = self.db.get_state("alert_manager", "main_state")
        if state:
            return state
        
        state = {}
        for pattern in VIP_PATTERNS:
            state[pattern.id] = {
                "last_processed_id": 0,
                "threshold_alerts": {}
            }
        return state

    def _save_state(self):
        self.db.set_state("alert_manager", "main_state", self.state)

    def check_all_patterns(self) -> list[Alert]:
        all_alerts = []
        current_max_id = self.db.get_max_id()
        if not current_max_id:
            return []

        for pattern in VIP_PATTERNS:
            alerts = self.check_pattern(pattern, current_max_id)
            all_alerts.extend(alerts)
        
        self._save_state()
        return all_alerts

    def check_pattern(self, pattern: Pattern, current_max_id: int) -> list[Alert]:
        alerts = []
        p_state = self.state.setdefault(pattern.id, {"last_processed_id": 0, "threshold_alerts": {}})
        
        # 1. Obtener última aparición real conocida en BD
        last_occurrence_id = self.db.get_last_occurrence_id(pattern.value)
        if last_occurrence_id is None:
            return []

        # Si es la primera vez, sincronizamos
        if p_state["last_processed_id"] == 0:
            p_state["last_processed_id"] = current_max_id
            return []

        # --- LÓGICA 1: DETECCIÓN DE SALIDA (WIN) ---
        if last_occurrence_id > p_state["last_processed_id"]:
            # ¡Salió el patrón! Buscamos la distancia oficial en el JSON del Tracker
            official_distance = self._get_official_distance(pattern.id, last_occurrence_id)
            
            if official_distance is not None:
                # Evaluamos ventanas
                for threshold in pattern.thresholds:
                    w_start, w_end = get_window_range(threshold)
                    
                    # Lógica Estricta: Solo alertar si cayó DENTRO de la ventana
                    if w_start <= official_distance <= w_end:
                        details = self._get_hit_details(pattern, last_occurrence_id)
                        alerts.append(Alert(
                            type=AlertType.PATTERN_HIT,
                            pattern_id=pattern.id,
                            pattern_name=pattern.name,
                            threshold=threshold,
                            spin_count=official_distance, # Distancia REAL del Tracker
                            timestamp=datetime.now(),
                            details=details
                        ))
                        logger.info(f"🎉 [{pattern.name}] WIN en Ventana [{w_start}-{w_end}] (Distancia Oficial: {official_distance})")

            # Actualizamos puntero y reseteamos avisos
            p_state["last_processed_id"] = current_max_id
            p_state["threshold_alerts"] = {} 
            return alerts

        # --- LÓGICA 2: AVISO DE UMBRAL (WARNING) ---
        current_wait = current_max_id - last_occurrence_id
        
        for threshold in pattern.thresholds:
            threshold_key = str(threshold)
            
            if current_wait >= threshold and not p_state["threshold_alerts"].get(threshold_key):
                alerts.append(Alert(
                    type=AlertType.THRESHOLD_REACHED,
                    pattern_id=pattern.id,
                    pattern_name=pattern.name,
                    threshold=threshold,
                    spin_count=current_wait,
                    timestamp=datetime.now(),
                    details={}
                ))
                logger.info(f"🔔 [{pattern.name}] UMBRAL {threshold} ALCANZADO (Espera: {current_wait})")
                p_state["threshold_alerts"][threshold_key] = True

        # Actualizamos puntero general
        p_state["last_processed_id"] = current_max_id
        
        return alerts

    def _get_official_distance(self, pattern_id: str, spin_id: int) -> Optional[int]:
        """Lee el JSON generado por PatternTracker para obtener la distancia oficial."""
        filepath = os.path.join(self.distances_dir, f"{pattern_id}.json")
        if not os.path.exists(filepath):
            return None
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            # Buscar la ocurrencia específica
            # Como se agregan al final, buscamos desde el último
            for occ in reversed(data.get("occurrences", [])):
                if occ["spin_id"] == spin_id:
                    return occ["distance_from_previous"]
                if occ["spin_id"] < spin_id: # Ya nos pasamos
                    break
        except Exception as e:
            logger.error(f"Error leyendo distancia oficial: {e}")
        return None

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

    def reset_states(self):
        self.state = {}
        self._save_state()
