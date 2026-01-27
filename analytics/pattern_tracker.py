"""
analytics/pattern_tracker.py - Tracking de distancias entre apariciones.
"""

import os
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional

from config.patterns import ALL_PATTERNS, Pattern
from core.database import Database

logger = logging.getLogger(__name__)

@dataclass
class PatternOccurrence:
    spin_id: int
    timestamp: str
    distance_from_previous: Optional[int]
    details: dict = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}

class PatternTracker:
    """Rastrea y registra distancias entre apariciones."""

    def __init__(self, db_path: str = "data/db.sqlite3"):
        self.db = Database(db_path)
        self.data_dir = "data/distances"
        self.state_file = "data/.tracker_state.json"
        os.makedirs(self.data_dir, exist_ok=True)
        self.state = self._load_state()

    def _load_state(self) -> dict:
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error cargando estado del tracker: {e}")
        return {
            "last_processed_id": 0,
            "last_result": None,
            "pattern_states": {
                pattern.id: {"last_id": None, "occurrences_count": 0}
                for pattern in ALL_PATTERNS
            }
        }

    def _save_state(self):
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, "w") as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logger.error(f"Error guardando estado del tracker: {e}")

    def process_new_spins(self) -> int:
        last_id = self.state["last_processed_id"]
        new_spins = self.db.get_spins_after_id(last_id)
        if not new_spins:
            return 0
        logger.info(f"📊 Tracker: Procesando {len(new_spins)} tiros nuevos")
        for spin in new_spins:
            self._process_spin(spin)
        self._save_state()
        return len(new_spins)

    def _process_spin(self, spin: dict):
        spin_id = spin["id"]
        resultado = spin["resultado"]
        for pattern in ALL_PATTERNS:
            if pattern.type == "simple" and resultado == pattern.value:
                self._record_occurrence(pattern, spin)
        if self.state["last_result"] is not None:
            for pattern in ALL_PATTERNS:
                if pattern.type == "sequence":
                    step1, step2 = pattern.value
                    if self.state["last_result"] == step1 and resultado == step2:
                        self._record_occurrence(pattern, spin)
        self.state["last_processed_id"] = spin_id
        self.state["last_result"] = resultado

    def _record_occurrence(self, pattern: Pattern, spin: dict):
        spin_id = spin["id"]
        pattern_state = self.state["pattern_states"][pattern.id]
        last_id = pattern_state["last_id"]

        # CAMBIO 2: Si last_id es None, buscar en BD última aparición
        if last_id is None:
            # Solo buscar en BD para patrones simples
            if pattern.type == "simple":
                db_last_id = self.db.get_last_occurrence_id(pattern.value)
                if db_last_id is not None:
                    last_id = db_last_id
                    logger.info(f"🔍 [{pattern.name}] Recuperando última aparición de BD: ID {last_id}")
                else:
                    logger.info(f"⚪ [{pattern.name}] Primera aparición en ID {spin_id} (calibrando)")
            else:
                # Para secuencias, siempre calibrar desde cero
                logger.info(f"⚪ [{pattern.name}] Primera aparición en ID {spin_id} (calibrando)")


        # Calcular distancia usando COUNT(*) real entre IDs
        if last_id is not None:
            # Contar giros reales entre last_id y spin_id (excluyendo extremos)
            cursor = self.db.get_connection().cursor()
            cursor.execute("SELECT COUNT(*) FROM tiros WHERE id > ? AND id <= ?", (last_id, spin_id))
            distance = cursor.fetchone()[0]
            cursor.close()
            logger.info(f"✅ [{pattern.name}] Aparición en ID {spin_id} (distancia: {distance})")
        else:
            distance = None

        occurrence = PatternOccurrence(
            spin_id=spin_id,
            timestamp=spin["timestamp"],
            distance_from_previous=distance,
            details=self._extract_details(pattern, spin)
        )
        self._save_occurrence(pattern, occurrence)
        pattern_state["last_id"] = spin_id
        pattern_state["occurrences_count"] += 1

    def _extract_details(self, pattern: Pattern, spin: dict) -> dict:
        details = {
            "resultado": spin["resultado"],
            "top_slot_matched": spin.get("is_top_slot_matched", False),
            "top_slot_multiplier": spin.get("top_slot_multiplier")
        }
        if pattern.value == "Pachinko":
            details["bonus_multiplier"] = spin.get("bonus_multiplier")
        elif pattern.value == "CrazyTime":
            details["flapper_blue"] = spin.get("ct_flapper_blue")
            details["flapper_green"] = spin.get("ct_flapper_green")
            details["flapper_yellow"] = spin.get("ct_flapper_yellow")
        return details

    def _save_occurrence(self, pattern: Pattern, occurrence: PatternOccurrence):
        filepath = os.path.join(self.data_dir, f"{pattern.id}.json")
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                data = json.load(f)
        else:
            data = {
                "pattern_id": pattern.id,
                "pattern_name": pattern.name,
                "occurrences": [],
                "distances": [],
                "statistics": {}
            }
        data["occurrences"].append(asdict(occurrence))
        if occurrence.distance_from_previous is not None:
            data["distances"].append(occurrence.distance_from_previous)
        if data["distances"]:
            import statistics
            data["statistics"] = {
                "count": len(data["distances"]),
                "mean": round(statistics.mean(data["distances"]), 2),
                "median": round(statistics.median(data["distances"]), 2),
                "min": min(data["distances"]),
                "max": max(data["distances"])
            }
        with open(filepath, "w") as f:
            json.dump(data, f, separators=(",", ":"))

    def get_pattern_distances(self, pattern_id: str, limit: Optional[int] = None) -> list[int]:
        filepath = os.path.join(self.data_dir, f"{pattern_id}.json")
        if not os.path.exists(filepath):
            return []
        with open(filepath, "r") as f:
            data = json.load(f)
        distances = data.get("distances", [])
        if limit:
            return distances[-limit:]
        return distances

    def get_pattern_statistics(self, pattern_id: str) -> dict:
        filepath = os.path.join(self.data_dir, f"{pattern_id}.json")
        if not os.path.exists(filepath):
            return {}
        with open(filepath, "r") as f:
            data = json.load(f)
        return data.get("statistics", {})
