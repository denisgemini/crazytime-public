"""
analytics/window_analyzer.py - Auditoría histórica de ventanas desde SQLite (v3.0).
"""

import os
import json
import logging
import statistics
from datetime import datetime
from typing import Optional, List, Dict

from config.patterns import Pattern, VIP_PATTERNS, get_window_range
from core.database import Database

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

logger = logging.getLogger(__name__)

class WindowAnalyzer:
    """Analizador histórico de rentabilidad de ventanas usando la BD."""

    def __init__(self, db_path: str = "data/db.sqlite3"):
        self.db = Database(db_path)
        self.results_dir = "data/analytics"
        os.makedirs(self.results_dir, exist_ok=True)

    def analyze_all_patterns(self) -> dict:
        logger.info("📊 Iniciando análisis de ventanas histórico (Pure SQLite)...")
        all_results = {}
        for pattern in VIP_PATTERNS:
            results = self.analyze_pattern(pattern)
            all_results[pattern.id] = results
        self._save_consolidated_report(all_results)
        return all_results

    def analyze_pattern(self, pattern: Pattern) -> dict:
        logger.info(f"🔍 Analizando ventanas para {pattern.name}...")
        
        # 1. Obtener todas las ocurrencias desde la BD
        occurrences = self._get_occurrences_from_db(pattern)
        
        results = {
            "pattern_id": pattern.id,
            "pattern_name": pattern.name,
            "windows": {},
            "analyzed_at": datetime.now().isoformat()
        }

        if len(occurrences) < 2:
            logger.warning(f"⚠️ Datos insuficientes para {pattern.name}")
            return results
            
        # 2. Analizar cada ventana configurada
        for threshold in pattern.warning_thresholds:
            window_result = self._analyze_window_zone(pattern, threshold, occurrences)
            window_key = window_result['window_range']
            results["windows"][window_key] = window_result
            
            logger.info(f"  Ventana {window_key}: Win Rate={window_result['win_rate']:.1f}%, ROI={window_result['roi']:+.1f}%")
            
        self._save_pattern_report(pattern, results)
        if HAS_OPENPYXL:
            self._generate_excel_report(pattern, results, occurrences)
            
        return results

    def _get_occurrences_from_db(self, pattern: Pattern) -> List[Dict]:
        """Extrae todas las apariciones y sus detalles de la tabla tiros."""
        with self.db.get_connection(read_only=True) as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id as spin_id, timestamp, resultado,
                       bonus_multiplier, top_slot_multiplier, is_top_slot_matched,
                       ct_flapper_blue, ct_flapper_green, ct_flapper_yellow
                FROM tiros WHERE resultado = ? ORDER BY id ASC
            """, (pattern.value,))
            rows = cur.fetchall()
            
            occs = []
            for i, row in enumerate(rows):
                d = dict(row)
                # Calcular distancia cronológica
                d["distance_from_previous"] = (row["spin_id"] - rows[i-1]["spin_id"]) if i > 0 else None
                # Formatear detalles para compatibilidad con lógica de pago
                d["details"] = {
                    "bonus_multiplier": d.get("bonus_multiplier"),
                    "top_slot_multiplier": d.get("top_slot_multiplier"),
                    "is_top_slot_matched": d.get("is_top_slot_matched"),
                    "ct_flapper_blue": d.get("ct_flapper_blue"),
                    "ct_flapper_green": d.get("ct_flapper_green"),
                    "ct_flapper_yellow": d.get("ct_flapper_yellow")
                }
                occs.append(d)
            return occs

    def _analyze_window_zone(self, pattern: Pattern, threshold: int, occurrences: list[dict]) -> dict:
        w_start, w_end = get_window_range(threshold)
        entries, wins, total_payout = 0, 0, 0
        
        for i in range(len(occurrences) - 1):
            dist = occurrences[i+1]["distance_from_previous"]
            if dist is None: continue
                
            if dist >= w_start:
                entries += 1
                if dist <= w_end:
                    wins += 1
                    total_payout += self._calculate_payout(pattern, occurrences[i+1]["details"])

        win_rate = (wins / entries * 100) if entries > 0 else 0
        window_size = (w_end - w_start + 1)
        total_invested = entries * window_size 
        profit_loss = total_payout - total_invested
        roi = (profit_loss / total_invested * 100) if total_invested > 0 else 0
        
        return {
            "window_range": f"[{w_start}-{w_end}]",
            "entries": entries,
            "wins": wins,
            "losses": entries - wins,
            "win_rate": round(win_rate, 2),
            "roi": round(roi, 2),
            "profit_loss": round(profit_loss, 2)
        }

    def _calculate_payout(self, pattern: Pattern, details: dict) -> float:
        payout = 0
        if pattern.id == "pachinko":
            base = details.get("bonus_multiplier") or 0
            payout = base * (details.get("top_slot_multiplier") or 1) if details.get("is_top_slot_matched") else base
        elif pattern.id == "crazytime":
            blue = details.get("ct_flapper_blue") or 0
            green = details.get("ct_flapper_green") or 0
            yellow = details.get("ct_flapper_yellow") or 0
            base = (blue + green + yellow) / 3
            payout = base * (details.get("top_slot_multiplier") or 1) if details.get("is_top_slot_matched") else base
        return payout

    def _save_pattern_report(self, pattern: Pattern, results: dict):
        filepath = os.path.join(self.results_dir, f"{pattern.id}_window_analysis.json")
        with open(filepath, "w") as f:
            json.dump(results, f, indent=2)

    def _save_consolidated_report(self, all_results: dict):
        filepath = os.path.join(self.results_dir, "window_analysis_full.json")
        with open(filepath, "w") as f:
            json.dump(all_results, f, indent=2)

    def _generate_excel_report(self, pattern: Pattern, results: dict, occurrences: list[dict]):
        wb = Workbook()
        ws = wb.active
        ws.title = "Historial"
        ws.append(["ID", "Fecha", "Distancia", "Resultado"])
        for o in occurrences:
            ws.append([o["spin_id"], o["timestamp"], o["distance_from_previous"], "WIN" if o["distance_from_previous"] and any(get_window_range(t)[0] <= o["distance_from_previous"] <= get_window_range(t)[1] for t in pattern.warning_thresholds) else "-"])
        wb.save(os.path.join(self.results_dir, f"{pattern.id}_history.xlsx"))
