"""
alerting/alert_manager.py - Gestión de alertas para patrones VIP.
"""

import os
import json
import logging
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from config.patterns import Pattern, VIP_PATTERNS
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
    """Gestor de alertas para patrones VIP."""

    def __init__(self, db_path: str = "data/db.sqlite3"):
        self.db = Database(db_path)
        # self.state_file = "data/.alert_state.json" <-- DEPRECATED
        self.state = self._load_state()

    def _load_state(self) -> dict:
        # Intentar cargar desde BD
        state = self.db.get_state("alert_manager", "main_state")
        if state:
            return state

        # Fallback: Migración de archivo antiguo si existe
        legacy_file = "data/.alert_state.json"
        if os.path.exists(legacy_file):
            try:
                logger.info("📦 Migrando estado de Alertas desde JSON a BD...")
                with open(legacy_file, "r") as f:
                    state = json.load(f)
                self.db.set_state("alert_manager", "main_state", state)
                return state
            except Exception as e:
                logger.error(f"Error migrando estado de alertas: {e}")

        # Estado inicial por defecto
        state = {}
        for pattern in VIP_PATTERNS:
            state[pattern.id] = {
                "last_seen_id": None,
                "thresholds": {}
            }
            for threshold in pattern.thresholds:
                state[pattern.id]["thresholds"][str(threshold)] = {
                    "status": "idle",
                    "last_alert_time": None
                }
        return state

    def _save_state(self):
        self.db.set_state("alert_manager", "main_state", self.state)

    def check_all_patterns(self) -> list[Alert]:
        all_alerts = []
        for pattern in VIP_PATTERNS:
            alerts = self.check_pattern(pattern)
            all_alerts.extend(alerts)
        return all_alerts

    def check_pattern(self, pattern: Pattern) -> list[Alert]:
        alerts = []
        # 1. Obtener última aparición por ID Real
        last_real_id = self.db.get_last_occurrence_id(pattern.value)
        if last_real_id is None:
            return alerts
            
        pattern_state = self.state[pattern.id]
        if pattern_state.get("last_seen_id") is None:
            logger.info(f"⚪ [{pattern.name}] Primera aparición detectada (calibrando ID Real {last_real_id})")
            pattern_state["last_seen_id"] = last_real_id
            self._save_state()
            return alerts

        # 2. Calcular espera actual usando IDs Reales
        max_id = self.db.get_max_id()
        current_wait = max_id - last_real_id

        # 3. Detectar si el patrón acaba de salir
        if last_real_id != pattern_state["last_seen_id"]:
            logger.info(f"🎉 [{pattern.name}] Salió en ID Real {last_real_id} (espera: {current_wait})")
            for threshold in pattern.thresholds:
                threshold_key = str(threshold)
                threshold_state = pattern_state["thresholds"][threshold_key]
                if threshold_state["status"] == "alerted":
                    # Usar ID real para obtener detalles
                    details = self._get_hit_details(pattern, last_real_id)
                    alerts.append(Alert(
                        type=AlertType.PATTERN_HIT,
                        pattern_id=pattern.id,
                        pattern_name=pattern.name,
                        threshold=threshold,
                        spin_count=current_wait,
                        timestamp=datetime.now(),
                        details=details
                    ))
                    logger.info(f"📤 [{pattern.name}] Alerta SALIDA (umbral {threshold}, salió en {current_wait})")
                    threshold_state["status"] = "idle"
                    threshold_state["last_alert_time"] = datetime.now().isoformat()

            pattern_state["last_seen_id"] = last_real_id
            self._save_state()
            return alerts

        # 4. Verificar si se alcanzó un umbral
        for threshold in pattern.thresholds:
            threshold_key = str(threshold)
            threshold_state = pattern_state["thresholds"][threshold_key]
            if current_wait >= threshold and threshold_state["status"] == "idle":
                alerts.append(Alert(
                    type=AlertType.THRESHOLD_REACHED,
                    pattern_id=pattern.id,
                    pattern_name=pattern.name,
                    threshold=threshold,
                    spin_count=current_wait,
                    timestamp=datetime.now(),
                    details={}
                ))
                logger.info(f"📤 [{pattern.name}] Alerta UMBRAL (umbral {threshold}, actual {current_wait})")
                threshold_state["status"] = "alerted"
                threshold_state["last_alert_time"] = datetime.now().isoformat()
        
        self._save_state()
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

    def reset_states(self):
        logger.warning("🔄 RESET: Reseteando estados de alertas")
        for pattern_id in self.state:
            self.state[pattern_id]["last_seen_id"] = None
            for threshold_key in self.state[pattern_id]["thresholds"]:
                self.state[pattern_id]["thresholds"][threshold_key]["status"] = "idle"
        self._save_state()
        logger.info("✅ Estados de alertas reseteados")
