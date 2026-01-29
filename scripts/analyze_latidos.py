"""
scripts/analyze_latidos.py - Auditoría de latidos con visibilidad de cortes de Android.
Categorías: 0-4s, 5s, 6-11s, >11s (Gaps) y Negativos.
Muestra los cortes más largos detectados.
"""

import sqlite3
import os
from datetime import datetime
from pathlib import Path

def analyze():
    root_dir = Path(__file__).resolve().parent.parent
    db_path = root_dir / "data" / "db.sqlite3"
    
    if not db_path.exists():
        print(f"❌ No se encuentra la base de datos en {db_path}")
        return

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    today = datetime.now().strftime('%Y-%m-%d')

    def get_data(where_clause="", params=()):
        cur.execute(f"SELECT id, latido, timestamp, resultado FROM tiros {where_clause} ORDER BY id DESC", params)
        return [dict(r) for r in cur.fetchall()]

    rows_today = get_data("WHERE timestamp LIKE ?", (f"{today}%",))
    rows_total = get_data()
    conn.close()

    def process_stats(rows):
        if not rows: return None
        s = {"0_4": 0, "5": 0, "6_11": 0, "gt11": 0, "neg": 0, "total": len(rows), "top_gaps": []}
        for r in rows:
            l = r['latido']
            if l < 0: s["neg"] += 1
            elif 0 <= l <= 4: s["0_4"] += 1
            elif l == 5: s["5"] += 1
            elif 6 <= l <= 11: s["6_11"] += 1
            else: s["gt11"] += 1
        
        # Obtener los 5 mayores gaps
        s["top_gaps"] = sorted(rows, key=lambda x: x['latido'], reverse=True)[:5]
        return s

    stats_today = process_stats(rows_today)
    stats_total = process_stats(rows_total)

    def print_report(s, title):
        print(f"\n📊 {title}")
        print("="*55)
        print(f" {'CATEGORÍA':<20} | {'CONTEO':>8} | {'PORCENTAJE':>10}")
        print("-" * 55)
        total = s["total"]
        print(f" 0 a 4 SEGUNDOS      | {s['0_4']:>8} | {(s['0_4']/total)*100:>9.1f}%")
        print(f" 5 SEGUNDOS          | {s['5']:>8} | {(s['5']/total)*100:>9.1f}%")
        print(f" 6 a 11 SEGUNDOS     | {s['6_11']:>8} | {(s['6_11']/total)*100:>9.1f}%")
        print(f" MAYORES A 11s (Gaps)| {s['gt11']:>8} | {(s['gt11']/total)*100:>9.1f}%")
        print(f" NEGATIVOS           | {s['neg']:>8} | {(s['neg']/total)*100:>9.1f}%")
        print("-" * 55)
        
        print(" 🕒 TOP 5 MAYORES CORTES (GAPS) DETECTADOS:")
        for i, g in enumerate(s["top_gaps"], 1):
            if g['latido'] > 11:
                h = g['latido'] // 3600
                m = (g['latido'] % 3600) // 60
                s_rem = g['latido'] % 60
                duration = f"{h}h {m}m {s_rem}s" if h > 0 else f"{m}m {s_rem}s"
                print(f"  {i}. {duration:<12} | ID {g['id']:<5} | {g['timestamp']}")
        
        print("="*55)

    if stats_today:
        print_report(stats_today, f"ESTADO DE HOY ({today})")
    
    if stats_total:
        print_report(stats_total, "RESUMEN HISTÓRICO TOTAL")

if __name__ == "__main__":
    analyze()
