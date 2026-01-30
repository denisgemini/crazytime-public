"""
analytics/pattern_tracker.py - Tracking de distancias en SQLite con memoria de hit (v3.1).
"""

import logging
from dataclasses import dataclass
from typing import Optional

from config.patterns import ALL_PATTERNS, Pattern
from core.database import Database

logger = logging.getLogger(__name__)

class PatternTracker:
    """Rastrea y registra distancias entre apariciones usando exclusivamente SQLite."""

    def __init__(self, db_path: str = "data/db.sqlite3"):
        self.db = Database(db_path)
        self.state = self._load_main_state()

    def _load_main_state(self) -> dict:
        """Carga el progreso global del tracker."""
        return self.db.get_state("pattern_tracker", "progress", {
            "last_processed_id": 0,
            "last_result": None
        })

    def _save_main_state(self):
        """Guarda el progreso global del tracker."""
        self.db.set_state("pattern_tracker", "progress", self.state)

    def process_new_spins(self) -> int:
        last_id = self.state.get("last_processed_id", 0)
        new_spins = self.db.get_spins_after_id(last_id)
        if not new_spins:
            return 0
            
        logger.info(f"📊 Tracker: Procesando {len(new_spins)} tiros nuevos")
        for spin in new_spins:
            self._process_spin(spin)
        
        # Al final del lote, actualizamos la distancia de espera actual para todos los patrones
        last_processed_id = new_spins[-1]["id"]
        for pattern in ALL_PATTERNS:
            p_data = self.db.get_state("pattern_tracker", pattern.id, {"last_id": None, "last_distance": 0, "prev_distance": 0})
            if p_data["last_id"] is not None:
                # Si el último tiro del lote NO fue el hit de este patrón, calculamos la espera real
                if p_data["last_id"] < last_processed_id:
                    p_data["last_distance"] = last_processed_id - p_data["last_id"]
                    self.db.set_state("pattern_tracker", pattern.id, p_data)
        
        self.state["last_processed_id"] = last_processed_id
        self._save_main_state()
        return len(new_spins)

    def _process_spin(self, spin: dict):
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
        
        self.state["last_result"] = resultado

    def _record_occurrence(self, pattern: Pattern, spin: dict):
        current_id = spin["id"]
        
        # Obtener estado individual del patrón desde SQLite
        p_data = self.db.get_state("pattern_tracker", pattern.id, {"last_id": None, "last_distance": 0, "prev_distance": 0})
        last_id = p_data.get("last_id")
        
        distance = 0
        if last_id is not None:
            distance = current_id - last_id
            logger.info(f"✅ [{pattern.name}] Aparición en ID {current_id} (distancia: {distance})")
        else:
            logger.info(f"⚪ [{pattern.name}] Primera aparición en ID {current_id} (calibrando)")

        # MANDATO: En HIT, last_distance = 0 y prev_distance = distancia real
        new_state = {
            "last_id": current_id,
            "last_distance": 0,
            "prev_distance": distance
        }
        self.db.set_state("pattern_tracker", pattern.id, new_state)

    def get_pattern_state(self, pattern_id: str) -> dict:
        """Obtiene el estado completo de un patrón."""
        return self.db.get_state("pattern_tracker", pattern_id, {"last_id": None, "last_distance": 0, "prev_distance": 0})
