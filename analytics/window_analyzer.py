"""
analytics/window_analyzer.py - Análisis de ventanas de apuesta.
"""

import os
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from config.patterns import Pattern, VIP_PATTERNS, WINDOW_CONFIG, get_window_range
from core.database import Database

logger = logging.getLogger(__name__)

@dataclass
class WindowResult:
    pattern_id: str
    pattern_name: str
    threshold: int
    window_start_offset: int
    window_end_offset: int
    total_opportunities: int
    hits_in_window: int
    misses: int
    hit_rate: float
    avg_payout: float
    total_payout: float
    total_invested: float
    profit_loss: float
    roi: float

class WindowAnalyzer:
    """Analizador de ventanas de apuesta."""

    def __init__(self, db_path: str = "data/db.sqlite3"):
        self.db = Database(db_path)
        self.results_dir = "data/analytics"
        os.makedirs(self.results_dir, exist_ok=True)

    def analyze_all_patterns(self) -> dict:
        logger.info("📊 Iniciando análisis de ventanas...")
        all_results = {}
        for pattern in VIP_PATTERNS:
            results = self.analyze_pattern(pattern)
            all_results[pattern.id] = results
        self._save_consolidated_report(all_results)
        return all_results

    def analyze_pattern(self, pattern: Pattern) -> dict:
        logger.info(f"🔍 Analizando {pattern.name}...")
        results = {
            "pattern_id": pattern.id,
            "pattern_name": pattern.name,
            "thresholds": {},
            "analyzed_at": datetime.now().isoformat()
        }
        occurrences = self._get_occurrences(pattern)
        if len(occurrences) < 2:
            logger.warning(f"⚠️ Datos insuficientes para {pattern.name}")
            return results
        for threshold in pattern.thresholds:
            window_result = self._analyze_threshold(pattern, threshold, occurrences)
            results["thresholds"][str(threshold)] = window_result
            logger.info(f"  Umbral {threshold}: Hit Rate={window_result['hit_rate']:.1f}%, ROI={window_result['roi']:+.1f}%")
        self._save_pattern_report(pattern, results)
        self._generate_excel_report(pattern, results, occurrences)
        return results

    def _analyze_threshold(self, pattern: Pattern, threshold: int, occurrences: list[dict]) -> dict:
        window_start_offset, window_end_offset = get_window_range(threshold)
        opportunities = 0
        hits = 0
        total_payout = 0
        for i in range(len(occurrences) - 1):
            current = occurrences[i]
            next_occ = occurrences[i + 1]
            distance = next_occ.get("distance_from_previous")
            if distance is None or distance < threshold:
                continue
            opportunities += 1
            current_id = current["spin_id"]
            window_start_id = current_id + window_start_offset
            window_end_id = current_id + window_end_offset
            next_id = next_occ["spin_id"]
            if window_start_id <= next_id <= window_end_id:
                hits += 1
                payout = self._calculate_payout(pattern, next_occ["details"])
                total_payout += payout
        misses = opportunities - hits
        hit_rate = (hits / opportunities * 100) if opportunities > 0 else 0
        avg_payout = (total_payout / hits) if hits > 0 else 0
        window_size = WINDOW_CONFIG["window_size"]
        total_invested = opportunities * window_size
        profit_loss = total_payout - total_invested
        roi = (profit_loss / total_invested * 100) if total_invested > 0 else 0
        return {
            "threshold": threshold,
            "window_start_offset": window_start_offset,
            "window_end_offset": window_end_offset,
            "window_size": window_size,
            "total_opportunities": opportunities,
            "hits_in_window": hits,
            "misses": misses,
            "hit_rate": round(hit_rate, 2),
            "avg_payout": round(avg_payout, 2),
            "total_payout": round(total_payout, 2),
            "total_invested": total_invested,
            "profit_loss": round(profit_loss, 2),
            "roi": round(roi, 2)
        }

    def _get_occurrences(self, pattern: Pattern) -> list[dict]:
        filepath = f"data/distances/{pattern.id}.json"
        if not os.path.exists(filepath):
            return []
        with open(filepath, "r") as f:
            data = json.load(f)
        return data.get("occurrences", [])

    def _calculate_payout(self, pattern: Pattern, details: dict) -> float:
        payout = 0
        if pattern.id == "pachinko":
            base = details.get("bonus_multiplier") or 0
            payout = base
            if details.get("top_slot_matched"):
                ts = details.get("top_slot_multiplier") or 1
                payout *= ts
        elif pattern.id == "crazytime":
            blue = details.get("flapper_blue") or 0
            green = details.get("flapper_green") or 0
            yellow = details.get("flapper_yellow") or 0
            base = (blue + green + yellow) / 3
            payout = base
            if details.get("top_slot_matched"):
                ts = details.get("top_slot_multiplier") or 1
                payout *= ts
        return payout

    def _save_pattern_report(self, pattern: Pattern, results: dict):
        filepath = os.path.join(self.results_dir, f"{pattern.id}_window_analysis.json")
        with open(filepath, "w") as f:
            json.dump(results, f, indent=2)
        logger.debug(f"📄 JSON guardado: {filepath}")

    def _save_consolidated_report(self, all_results: dict):
        filepath = os.path.join(self.results_dir, "window_analysis_full.json")
        with open(filepath, "w") as f:
            json.dump(all_results, f, indent=2)
        logger.info(f"📄 Reporte consolidado: {filepath}")

    def _generate_excel_report(self, pattern: Pattern, results: dict, occurrences: list[dict]):
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill
            wb = Workbook()
            ws_summary = wb.active
            ws_summary.title = "Resumen"
            headers = ["Umbral", "Ventana Inicio", "Ventana Fin", "Oportunidades", "Aciertos", "Fallos", "Hit Rate %", "Pago Promedio", "ROI %", "Ganancia/Pérdida"]
            ws_summary.append(headers)
            for cell in ws_summary[1]:
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="366092", fill_type="solid")
                cell.font = Font(bold=True, color="FFFFFF")
            for threshold_str, data in results["thresholds"].items():
                row = [data["threshold"], data["window_start_offset"], data["window_end_offset"],
                       data["total_opportunities"], data["hits_in_window"], data["misses"],
                       data["hit_rate"], data["avg_payout"], data["roi"], data["profit_loss"]]
                ws_summary.append(row)
            ws_detail = wb.create_sheet("Detalle por Oportunidad")
            detail_headers = ["ID Aparición", "Fecha", "Distancia", "Umbral", "En Ventana?", "Pago", "Detalles Bonus"]
            ws_detail.append(detail_headers)
            for cell in ws_detail[1]:
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="366092", fill_type="solid")
                cell.font = Font(bold=True, color="FFFFFF")
            for i in range(len(occurrences) - 1):
                current = occurrences[i]
                next_occ = occurrences[i + 1]
                distance = next_occ.get("distance_from_previous")
                if distance is None:
                    continue
                threshold_reached = None
                for t in pattern.thresholds:
                    if distance >= t:
                        threshold_reached = t
                if threshold_reached is None:
                    continue
                window_start, window_end = get_window_range(threshold_reached)
                current_id = current["spin_id"]
                next_id = next_occ["spin_id"]
                in_window = (current_id + window_start <= next_id <= current_id + window_end)
                payout = 0
                if in_window:
                    payout = self._calculate_payout(pattern, next_occ["details"])
                details_str = self._format_bonus_details(pattern, next_occ["details"])
                row = [next_id, next_occ["timestamp"], distance, threshold_reached, "SÍ" if in_window else "NO", payout, details_str]
                ws_detail.append(row)
            excel_path = os.path.join(self.results_dir, f"{pattern.id}_window_analysis.xlsx")
            wb.save(excel_path)
            logger.info(f"📊 Excel generado: {excel_path}")
        except ImportError:
            logger.warning("⚠️ openpyxl no instalado, omitiendo Excel")
        except Exception as e:
            logger.error(f"Error generando Excel: {e}")

    def _format_bonus_details(self, pattern: Pattern, details: dict) -> str:
        if pattern.id == "pachinko":
            bonus = details.get("bonus_multiplier", 0)
            ts = details.get("top_slot_multiplier", 0) if details.get("top_slot_matched") else 0
            if ts:
                return f"Bonus: {bonus}x, TS: {ts}x"
            return f"Bonus: {bonus}x"
        elif pattern.id == "crazytime":
            blue = details.get("flapper_blue", 0)
            green = details.get("flapper_green", 0)
            yellow = details.get("flapper_yellow", 0)
            ts = details.get("top_slot_multiplier", 0) if details.get("top_slot_matched") else 0
            base = f"B:{blue} G:{green} Y:{yellow}"
            if ts:
                base += f" TS:{ts}x"
            return base
        return ""
