"""
alerting/alert_manager.py - Gestión de alertas con umbrales y detección de hits.

Versionado: Git y GitHub únicamente.
No se versiona manualmente en código.
"""

import logging
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

from config.patterns import Pattern, VIP_PATTERNS
from core.database import Database

logger = logging.getLogger(__name__)

class AlertType(Enum):
    THRESHOLD_REACHED = "threshold_reached"  # Aviso de umbral alcanzado
    PATTERN_HIT = "pattern_hit"              # Salida detectada en ventana

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
    """Gestor de alertas basado en SQLite."""

    def __init__(self, db_path: str = "data/db.sqlite3"):
        self.db = Database(db_path)
        self.state = self._load_state()

    def _load_state(self) -> dict:
        """Carga la memoria de alertas enviadas desde BD."""
        return self.db.get_state("alert_manager", "main_state", {})

    def _save_state(self):
        """Guarda la memoria de alertas enviadas en BD."""
        self.db.set_state("alert_manager", "main_state", self.state)

    def check_all_patterns(self) -> list[Alert]:
        """Revisa todos los patrones VIP y genera alertas si corresponde."""
        all_alerts = []
        current_max_id = self.db.get_max_id()
        if not current_max_id:
            return []

        for pattern in VIP_PATTERNS:
            # Leer estado del pattern_tracker desde BD
            tracker_data = self.db.get_state("pattern_tracker", pattern.id,
                                           {"last_id": None, "last_distance": 0, "prev_distance": 0})

            if tracker_data["last_id"]:
                alerts = self.check_pattern(pattern, current_max_id, tracker_data)
                all_alerts.extend(alerts)

        self._save_state()
        return all_alerts

    def check_pattern(self, pattern: Pattern, current_max_id: int, tracker_data: dict) -> list[Alert]:
        """Revisa un patrón específico y genera alertas de umbrales y hits."""
        alerts = []
        tracker_last_id = tracker_data.get("last_id")
        last_distance = tracker_data.get("last_distance", 0)
        prev_distance = tracker_data.get("prev_distance", 0)

        # Inicializar estado del patrón en alert_manager
        p_state = self.state.setdefault(pattern.id, {
            "last_processed_id": tracker_last_id,
            "alerts_sent": {}
        })

        # Detectar si hubo hit en este ciclo
        is_hit = tracker_last_id > p_state["last_processed_id"]

        # Determinar distancia y punto de inicio para cálculos
        if is_hit:
            # Cuando hay hit, usamos prev_distance (la racha que acaba de terminar)
            distance_for_thresholds = prev_distance
            start_id = tracker_last_id - prev_distance
        else:
            # Sin hit, usamos last_distance (racha actual en curso)
            distance_for_thresholds = last_distance
            start_id = tracker_last_id

        # ============================================================
        # BLOQUE 1: ALERTAS DE UMBRALES
        # ============================================================
        for threshold in pattern.warning_thresholds:
            t_key = str(threshold)
            
            # Verificar si se alcanzó el umbral y no se ha enviado alerta
            if distance_for_thresholds >= threshold and not p_state["alerts_sent"].get(t_key):
                # Calcular ID exacto del tiro que cruzó el umbral
                threshold_spin_id = start_id + threshold
                
                # Buscar timestamp del tiro en BD
                spin_data = self.db.get_spin_by_id(threshold_spin_id)
                
                if spin_data and spin_data.get("timestamp"):
                    try:
                        alert_time = datetime.fromisoformat(spin_data["timestamp"])
                    except Exception as e:
                        logger.warning(f"Error parseando timestamp para umbral {threshold}: {e}. Usando hora actual.")
                        alert_time = datetime.now()
                else:
                    # Fallback: si no se encuentra el tiro, usar hora actual
                    logger.warning(f"No se encontró tiro #{threshold_spin_id} en BD. Usando hora actual para alerta.")
                    alert_time = datetime.now()
                
                # Crear y registrar alerta
                alerts.append(Alert(
                    type=AlertType.THRESHOLD_REACHED,
                    pattern_id=pattern.id,
                    pattern_name=pattern.name,
                    value=threshold,
                    spin_count=distance_for_thresholds,
                    timestamp=alert_time,
                    details={}
                ))
                logger.info(f"🔔 [{pattern.name}] UMBRAL {threshold} alcanzado (Distancia: {distance_for_thresholds})")
                p_state["alerts_sent"][t_key] = True

        # ============================================================
        # BLOQUE 2: ALERTAS DE HITS (Salidas)
        # ============================================================
        if is_hit:
            # Solo alertar si la salida está en ventana de apuesta (primera ventana o más)
            if prev_distance > 0 and pattern.betting_windows:
                start_game_zone = pattern.betting_windows[0][0]
                
                if prev_distance >= start_game_zone:
                    # Buscar datos del hit en BD
                    spin_data = self.db.get_spin_by_id(tracker_last_id)
                    
                    # Extraer hora y detalles
                    if spin_data and spin_data.get("timestamp"):
                        try:
                            hit_time = datetime.fromisoformat(spin_data["timestamp"])
                        except:
                            hit_time = datetime.now()
                    else:
                        hit_time = datetime.now()
                    
                    # Construir detalles según el patrón
                    details = {"resultado": spin_data.get("resultado", "Unknown") if spin_data else "Unknown"}
                    
                    if spin_data:
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
                    
                    # Crear y registrar alerta de hit
                    alerts.append(Alert(
                        type=AlertType.PATTERN_HIT,
                        pattern_id=pattern.id,
                        pattern_name=pattern.name,
                        value=prev_distance,
                        spin_count=prev_distance,
                        timestamp=hit_time,
                        details=details
                    ))
                    logger.info(f"🎉 [{pattern.name}] SALIDA detectada (Distancia: {prev_distance})")

            # Resetear memoria de umbrales tras el hit
            p_state["alerts_sent"] = {}
            p_state["last_processed_id"] = tracker_last_id

        return alerts

