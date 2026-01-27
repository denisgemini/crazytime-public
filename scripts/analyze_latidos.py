
import sqlite3
from datetime import datetime
from collections import Counter

def analyze():
    conn = sqlite3.connect('data/db.sqlite3')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Traemos todos los tiros ordenados por ID
    cur.execute("SELECT id, resultado, timestamp, started_at FROM tiros ORDER BY id ASC")
    rows = cur.fetchall()
    
    latidos = []
    last_timestamp = None
    
    for row in rows:
        current_started = row['started_at']
        
        if last_timestamp and current_started:
            try:
                # Calculamos el latido: started_at actual - timestamp anterior
                t1 = datetime.fromisoformat(last_timestamp)
                t2 = datetime.fromisoformat(current_started)
                diff = int((t2 - t1).total_seconds())
                latidos.append(diff)
            except Exception:
                pass
        
        last_timestamp = row['timestamp']
    
    conn.close()
    
    print(f"{'ID':>5} | {'Resultado':>12} | {'Started At':>20} | {'Prev Timestamp':>20} | {'Latido':>8}")
    print("-" * 75)
    
    for i in range(1, len(rows)):
        current = rows[i]
        prev = rows[i-1]
        
        if current['started_at'] and prev['timestamp']:
            try:
                t1 = datetime.fromisoformat(prev['timestamp'])
                t2 = datetime.fromisoformat(current['started_at'])
                diff = int((t2 - t1).total_seconds())
                
                if diff < 0:
                    print(f"{current['id']:>5} | {current['resultado']:>12} | {current['started_at']:>20} | {prev['timestamp']:>20} | {diff:>8}")
                    # También mostramos el anterior para comparar
                    print(f"{prev['id']:>5} | {prev['resultado']:>12} | {prev['started_at']:>20} | {prev['timestamp']:>20} | (ANTERIOR)")
                    print("-" * 75)
            except Exception:
                pass


if __name__ == "__main__":
    analyze()
