"""
analytics/window_analyzer.py - Análisis profundo de ventanas de apuesta.
Enfoque: Rentabilidad histórica de VENTANAS (Entries/Wins/Losses).
"""

import os
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from config.patterns import Pattern, VIP_PATTERNS, WINDOW_CONFIG, get_window_range
from core.database import Database

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

logger = logging.getLogger(__name__)

class WindowAnalyzer:
    """Analizador histórico de ventanas de apuesta."""

    def __init__(self, db_path: str = "data/db.sqlite3"):
        self.db = Database(db_path)
        self.results_dir = "data/analytics"
        os.makedirs(self.results_dir, exist_ok=True)

    def analyze_all_patterns(self) -> dict:
        logger.info("📊 Iniciando análisis de ventanas (Histórico)...")
        all_results = {}
        for pattern in VIP_PATTERNS:
            results = self.analyze_pattern(pattern)
            all_results[pattern.id] = results
        self._save_consolidated_report(all_results)
        return all_results

    def analyze_pattern(self, pattern: Pattern) -> dict:
        logger.info(f"🔍 Analizando ventanas para {pattern.name}...")
        results = {
            "pattern_id": pattern.id,
            "pattern_name": pattern.name,
            "windows": {}, # Reemplaza 'thresholds'
            "analyzed_at": datetime.now().isoformat()
        }
        occurrences = self._get_occurrences(pattern)
        if len(occurrences) < 2:
            logger.warning(f"⚠️ Datos insuficientes para {pattern.name}")
            return results
            
        for threshold in pattern.thresholds:
            window_result = self._analyze_window_zone(pattern, threshold, occurrences)
            window_key = f"[{window_result['window_start_offset']}-{window_result['window_end_offset']}]"
            results["windows"][window_key] = window_result
            
            logger.info(f"  Ventana {window_key}: Win Rate={window_result['win_rate']:.1f}%, ROI={window_result['roi']:+.1f}%")
            
        self._save_pattern_report(pattern, results)
        self._generate_excel_report(pattern, results, occurrences)
        return results

    def _analyze_window_zone(self, pattern: Pattern, threshold: int, occurrences: list[dict]) -> dict:
        w_start, w_end = get_window_range(threshold)
        
        entries = 0
        wins = 0
        losses = 0
        total_payout = 0
        
        # Iterar sobre pares de ocurrencias (Actual -> Siguiente)
        for i in range(len(occurrences) - 1):
            current = occurrences[i]
            next_occ = occurrences[i + 1]
            dist = next_occ.get("distance_from_previous")
            
            if dist is None:
                continue
                
            # LÓGICA ESTRICTA DE VENTANA
            # 1. ¿Llegamos a la zona?
            if dist < w_start:
                continue # Ignorar
                
            # Entramos
            entries += 1
            
            # 2. Resultado
            current_id = current["spin_id"]
            next_id = next_occ["spin_id"]
            target_start = current_id + w_start
            target_end = current_id + w_end
            
            if target_start <= next_id <= target_end:
                wins += 1
                payout = self._calculate_payout(pattern, next_occ["details"])
                total_payout += payout
            else:
                losses += 1

        win_rate = (wins / entries * 100) if entries > 0 else 0
        avg_payout = (total_payout / wins) if wins > 0 else 0
        
        window_size = WINDOW_CONFIG["window_size"]
        total_invested = entries * window_size # Costo por entrar a jugar la ventana completa
        profit_loss = total_payout - total_invested
        roi = (profit_loss / total_invested * 100) if total_invested > 0 else 0
        
        return {
            "window_range": f"[{w_start}-{w_end}]",
            "window_start_offset": w_start,
            "window_end_offset": w_end,
            "entries": entries,
            "wins": wins,
            "losses": losses,
            "win_rate": round(win_rate, 2),
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
        if not HAS_OPENPYXL:
            return
            
        try:
            wb = Workbook()
            ws_summary = wb.active
            ws_summary.title = "Resumen Ventanas"
            
            # Cabeceras centradas en Ventanas
            headers = ["Ventana", "Entradas (Intentos)", "Wins (Aciertos)", "Losses (Fallos)", "Win Rate %", "Pago Promedio", "ROI %", "Ganancia/Pérdida"]
            ws_summary.append(headers)
            
            for cell in ws_summary[1]:
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="366092", fill_type="solid")
                cell.font = Font(bold=True, color="FFFFFF")
                
            for w_key, data in results["windows"].items():
                row = [
                    w_key, 
                    data["entries"], 
                    data["wins"], 
                    data["losses"],
                    data["win_rate"], 
                    data["avg_payout"], 
                    data["roi"], 
                    data["profit_loss"]
                ]
                ws_summary.append(row)
                
            ws_detail = wb.create_sheet("Detalle Histórico")
            detail_headers = ["ID Aparición", "Fecha", "Distancia", "Ventana Jugada", "Resultado", "Pago", "Detalles"]
            ws_detail.append(detail_headers)
            
            for i in range(len(occurrences) - 1):
                current = occurrences[i]
                next_occ = occurrences[i + 1]
                dist = next_occ.get("distance_from_previous")
                
                if dist is None:
                    continue
                    
                # Determinar qué ventana se jugó (si alguna)
                played_window = None
                result_str = "-"
                
                for threshold in pattern.thresholds:
                    w_start, w_end = get_window_range(threshold)
                    if dist >= w_start:
                        played_window = f"[{w_start}-{w_end}]"
                        # Check result
                        current_id = current["spin_id"]
                        next_id = next_occ["spin_id"]
                        target_start = current_id + w_start
                        target_end = current_id + w_end
                        
                        if target_start <= next_id <= target_end:
                            result_str = "WIN ✅"
                        else:
                            result_str = "LOSS ❌"
                        break # Asumimos que solo juega la ventana más cercana que superó
                
                if played_window:
                    payout = self._calculate_payout(pattern, next_occ["details"]) if result_str == "WIN ✅" else 0
                    details_str = self._format_bonus_details(pattern, next_occ["details"])
                    
                    row = [
                        next_occ["spin_id"], 
                        next_occ["timestamp"], 
                        dist, 
                        played_window, 
                        result_str, 
                        payout, 
                        details_str
                    ]
                    ws_detail.append(row)
                    
            excel_path = os.path.join(self.results_dir, f"{pattern.id}_window_analysis.xlsx")
            wb.save(excel_path)
            logger.info(f"📊 Excel generado: {excel_path}")
            
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