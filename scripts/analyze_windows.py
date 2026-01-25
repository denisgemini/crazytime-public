"""
scripts/analyze_windows.py - Análisis manual de ventanas.
"""

import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics.window_analyzer import WindowAnalyzer
from analytics.pattern_tracker import PatternTracker
from config.patterns import VIP_PATTERNS

def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
    logger = logging.getLogger(__name__)
    logger.info("=" * 70)
    logger.info("📊 ANÁLISIS DE VENTANAS - CRAZYTIME")
    logger.info("=" * 70)
    try:
        tracker = PatternTracker("data/db.sqlite3")
        analyzer = WindowAnalyzer("data/db.sqlite3")
        results = analyzer.analyze_all_patterns()
        print("\n" + "=" * 70)
        print("RESUMEN DEL ANÁLISIS")
        print("=" * 70)
        for pattern in VIP_PATTERNS:
            pattern_results = results.get(pattern.id, {})
            thresholds = pattern_results.get("thresholds", {})
            print(f"\n{pattern.name.upper()}")
            print("-" * 70)
            for threshold_str, data in thresholds.items():
                print(f"\n  Umbral {threshold_str}:")
                print(f"    Ventana: tiros {data['window_start_offset']}-{data['window_end_offset']}")
                print(f"    Oportunidades: {data['total_opportunities']}")
                print(f"    Aciertos: {data['hits_in_window']} ({data['hit_rate']}%)")
                print(f"    ROI: {data['roi']:+.2f}%")
                print(f"    Ganancia/Pérdida: {data['profit_loss']:+.2f}")
        print("\n" + "=" * 70)
        print("✅ Análisis completado")
        print(f"📁 Reportes guardados en: data/analytics/")
        print("=" * 70)
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
