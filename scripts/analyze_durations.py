"""
scripts/analyze_durations.py - Analiza la duración real de los tiros.
Calcula (settled_at - started_at) para ver el tiempo de rotación de la rueda.
"""

import sqlite3
from datetime import datetime
import statistics

def analizar_duraciones():
    conn = sqlite3.connect('data/db.sqlite3')
    cur = conn.cursor()
    
    # Obtener tiempos de los últimos 500 tiros (para tener una muestra reciente)
    cur.execute("SELECT timestamp, settled_at, resultado FROM tiros WHERE settled_at IS NOT NULL ORDER BY id DESC LIMIT 500")
    rows = cur.fetchall()
    conn.close()
    
    if not rows:
        print("No hay datos suficientes para analizar duraciones.")
        return

    duraciones = []
    duraciones_por_tipo = {}

    for inicio_str, fin_str, resultado in rows:
        try:
            t_inicio = datetime.fromisoformat(inicio_str)
            t_fin = datetime.fromisoformat(fin_str)
            duracion = (t_fin - t_inicio).total_seconds()
            
            if 0 < duracion < 600:  # Ignorar errores absurdos
                duraciones.append(duracion)
                if resultado not in duraciones_por_tipo:
                    duraciones_por_tipo[resultado] = []
                duraciones_por_tipo[resultado].append(duracion)
        except:
            continue

    if not duraciones:
        print("No se pudieron calcular duraciones válidas.")
        return

    print("\n📊 ANÁLISIS DE DURACIÓN DE TIROS (Últimos 500)")
    print("-" * 45)
    print(f"Promedio General:  {statistics.mean(duraciones):.2f} segundos")
    print(f"Mínimo:            {min(duraciones):.2f} segundos")
    print(f"Máximo:            {max(duraciones):.2f} segundos")
    print(f"Mediana:           {statistics.median(duraciones):.2f} segundos")
    
    print("\n📈 PROMEDIO POR RESULTADO:")
    for res, docs in sorted(duraciones_por_tipo.items()):
        avg = statistics.mean(docs)
        print(f"  - {res:12}: {avg:.2f}s ({len(docs)} tiros)")

if __name__ == "__main__":
    analizar_duraciones()
