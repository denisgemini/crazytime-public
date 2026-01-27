
import sqlite3
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
import os

def generar_grafico_pillow():
    # 1. Obtener datos reales
    conn = sqlite3.connect('data/db.sqlite3')
    cur = conn.cursor()
    hace_24h = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S")
    cur.execute("SELECT latido FROM tiros WHERE timestamp >= ?", (hace_24h,))
    latidos = [row[0] for row in cur.fetchall()]
    conn.close()

    # 2. Clasificar
    stats = {'0-4s': 0, '5s': 0, '6-11s': 0, '>11s': 0}
    for l in latidos:
        if l <= 4: stats['0-4s'] += 1
        elif l == 5: stats['5s'] += 1
        elif l <= 11: stats['6-11s'] += 1
        else: stats['>11s'] += 1

    # 3. Dibujar imagen (600x400)
    img = Image.new('RGB', (600, 400), color='#1a1a1a')
    draw = ImageDraw.Draw(img)
    
    max_val = max(stats.values()) if stats.values() else 1
    colores = {'0-4s': '#ffbb33', '5s': '#00C851', '6-11s': '#33b5e5', '>11s': '#ff4444'}
    
    x_start = 50
    width = 100
    gap = 30
    
    for i, (label, val) in enumerate(stats.items()):
        # Calcular altura de barra
        h = (val / max_val) * 250
        x0 = x_start + i * (width + gap)
        y0 = 350 - h
        x1 = x0 + width
        y1 = 350
        
        # Dibujar barra
        draw.rectangle([x0, y0, x1, y1], fill=colores[label])
        
        # Etiquetas (Texto simple ya que no tenemos fuentes cargadas usualmente)
        draw.text((x0 + 30, 360), label, fill='white')
        draw.text((x0 + 30, y0 - 20), str(val), fill='white')

    draw.text((200, 20), f"SALUD DE LATIDOS - {datetime.now().strftime('%d/%m')}", fill='white')
    
    os.makedirs('data/analytics', exist_ok=True)
    img.save('data/analytics/salud_test.png')
    print("Imagen generada en data/analytics/salud_test.png")

if __name__ == "__main__":
    generar_grafico_pillow()
