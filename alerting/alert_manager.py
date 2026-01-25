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
        self.state_file = "data/.alert_state.json"
        self.state = self._load_state()

    def _load_state(self) -> dict:
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error cargando estado de alertas: {e}")
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
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, "w") as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logger.error(f"Error guardando estado de alertas: {e}")

    def check_all_patterns(self) -> list[Alert]:
        all_alerts = []
        for pattern in VIP_PATTERNS:
            alerts = self.check_pattern(pattern)
            all_alerts.extend(alerts)
        return all_alerts

    def check_pattern(self, pattern: Pattern) -> list[Alert]:
        alerts = []
        last_id = self.db.get_last_occurrence_id(pattern.value)
        if last_id is None:
            return alerts
        pattern_state = self.state[pattern.id]
        if pattern_state["last_seen_id"] is None:
            logger.info(f"⚪ [{pattern.name}] Primera aparición detectada (calibrando)")
            pattern_state["last_seen_id"] = last_id
            self._save_state()
            return alerts
        max_id = self.db.get_max_id()
        # Contar giros reales entre last_id y max_id (excluyendo extremos)
        cursor = self.db.get_connection().cursor()
        cursor.execute("SELECT COUNT(*) FROM tiros WHERE id > ? AND id <= ?", (last_id, max_id))
        current_wait = cursor.fetchone()[0]
        cursor.close()
        if last_id != pattern_state["last_seen_id"]:
            # CAMBIO 8: Validar gap antes de generar alerta
            if self._validate_gap(last_id, max_id):
                logger.info(f"🎉 [{pattern.name}] Salió en ID {last_id} (espera: {current_wait})")
                for threshold in pattern.thresholds:
                    threshold_key = str(threshold)
                    threshold_state = pattern_state["thresholds"][threshold_key]
                    if threshold_state["status"] == "alerted":
                        details = self._get_hit_details(pattern, last_id)
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
            else:
                logger.info(f"⏭️ [{pattern.name}] Omitiendo alerta por gap anómalo detectado")

            pattern_state["last_seen_id"] = last_id
            self._save_state()
            return alerts
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

    def _validate_gap(self, last_id: int, max_id: int) -> bool:
        """
        CAMBIO 8: Valida que no haya gaps anómalos (>11s) entre last_id y max_id.

        Returns:
            True si todos los gaps son normales, False si hay gaps anómalos
        """
        try:
            # Obtener tiros entre last_id y max_id (inclusive)
            spins = self.db.get_spins_after_id(last_id - 1)
            if not spins or len(spins) < 2:
                return True  # No hay suficientes datos para validar

            GAP_THRESHOLD = 11.0  # 5s normal + 6s tolerancia

            for i in range(len(spins) - 1):
                current = spins[i]
                next_spin = spins[i + 1]

                # Calcular gap: started_at del siguiente - timestamp del actual
                if not next_spin.get("started_at"):
                    continue

                try:
                    current_start = datetime.fromisoformat(next_spin["started_at"])
                    prev_ts = datetime.fromisoformat(current["timestamp"])
                    gap = (current_start - prev_ts).total_seconds()

                    if gap > GAP_THRESHOLD:
                        logger.warning(f"⚠️ Gap anómalo detectado: {gap:.1f}s entre ID {current['id']} y {next_spin['id']}")
                        return False  # Hay gap anómalo, no generar alerta
                except Exception as e:
                    logger.debug(f"Error validando gap: {e}")
                    continue

            return True  # Todos los gaps son normales

        except Exception as e:
            logger.error(f"Error en validación de gap: {e}")
            return True  # Si falla la validación, permitir alerta

    # CAMBIO 9: Método helper para obtener ocurrencias entre IDs
    def get_occurrences_between_ids(self, pattern: Pattern, start_id: int, end_id: int) -> list[dict]:
        """
        CAMBIO 9: Obtiene las ocurrencias de un patrón entre dos IDs.

        Args:
            pattern: El patrón a buscar
            start_id: ID inicial (exclusivo)
            end_id: ID final (inclusive)

        Returns:
            Lista de tiros que coinciden con el patrón en el rango especificado
        """
        try:
            spins = self.db.get_spins_after_id(start_id)
            result = []
            for spin in spins:
                if spin["id"] > end_id:
                    break
                if pattern.type == "simple" and spin["resultado"] == pattern.value:
                    result.append(spin)
                elif pattern.type == "sequence" and result:
                    # Para secuencias, verificar el par
                    prev_result = result[-1]["resultado"] if result else None
                    step1, step2 = pattern.value
                    if prev_result == step1 and spin["resultado"] == step2:
                        result.append(spin)
            return result
        except Exception as e:
            logger.error(f"Error obteniendo ocurrencias entre IDs: {e}")
            return []

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
