"""
scripts/analyze_brechas.py - Reporte de Brechas con Cuadros Unicode (v3.15)
Alineación Total y Conectores de Alta Precisión.
"""

import sys
import os
import sqlite3
import argparse
import unicodedata
from datetime import datetime, timedelta

DB_PATH = "data/db.sqlite3"
UMBRAL = 15
ANCHO_BOX = 50 

def get_disp_w(s):
    w = 0
    for c in s:
        cp = ord(c)
        if 0xFE00 <= cp <= 0xFE0F: continue
        if unicodedata.east_asian_width(c) in ('W', 'F', 'A') or 0x1F300 <= cp <= 0x1F9FF:
            w += 2
        else:
            w += 1
    return w

def pad_l(text, width, align='left'):
    curr_w = get_disp_w(text)
    needed = width - curr_w
    if needed <= 0: return text[:width]
    if align == 'left': return text + (' ' * needed)
    if align == 'right': return (' ' * needed) + text
    l = needed // 2
    r = needed - l
    return (' ' * l) + text + (' ' * r)

def bar(l='╔', m='═', r='╗'):
    print(f"{l}{m*(ANCHO_BOX-2)}{r}")

def row(text, align='left'):
    inner_w = ANCHO_BOX - 4
    print(f"║ {pad_l(text, inner_w, align)} ║")

def table_sep(widths, l='╠', m='╪', r='╣', char='═'):
    # Construcción precisa: l + (w1+2) + m + (w2+2) + m ... + r = 50
    linea = l + char * (widths[0] + 2)
    for w in widths[1:-1]:
        linea += m + char * (w + 2)
    linea += m + char * (widths[-1] + 2) + r
    print(linea)

def table_row(cells, widths):
    items = []
    for i in range(len(cells)):
        items.append(pad_l(str(cells[i]), widths[i], 'left'))
    contenido = " │ ".join(items)
    print(f"║ {pad_l(contenido, 46, 'left')} ║")

def get_esp_day(dt):
    dias = ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", "SÁBADO", "DOMINGO"]
    return dias[dt.weekday()]

def obtener_datos(periodo="hoy"):
    if not os.path.exists(DB_PATH): return [], None, None
    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        now = datetime.now()
        if periodo == "hoy": f_ini = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif periodo == "semana":
            f_ini = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            cur.execute("SELECT MIN(timestamp) FROM tiros"); min_ts = cur.fetchone()[0]
            try: f_ini = datetime.fromisoformat(min_ts)
            except: f_ini = now - timedelta(days=30)
        query = "SELECT timestamp, latido, datetime(timestamp, '-' || latido || ' seconds') as hora_inicio FROM tiros WHERE latido > ? AND timestamp >= ? ORDER BY timestamp ASC"
        cur.execute(query, (UMBRAL, f_ini.isoformat()))
        rows = cur.fetchall()
        conn.close()
        return rows, f_ini, now
    except: return [], None, None

def dur_b(seg):
    if seg < 60: return f"{seg}s"
    m, s = divmod(seg, 60)
    h, m = divmod(m, 60)
    if h > 0: return f"{h}h {m}m"
    return f"{m}m {s}s"

def get_cat_name(s):
    if s <= 60: return "1m", "1 min"
    if s <= 120: return "2m", "2 min"
    if s <= 180: return "3m", "3 min"
    if s <= 600: return "10m", "10 min"
    if s <= 900: return "15m", "15 min"
    if s <= 1800: return "30m", "30 min"
    return "RESTO", "El resto"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--periodo", type=str, default="hoy")
    args = parser.parse_args()
    rows, f_ini, f_fin = obtener_datos(args.periodo)
    if not f_ini: return

    tot_s = sum(r['latido'] for r in rows)
    delta = (f_fin - f_ini).total_seconds()
    integridad = 100 - (tot_s / delta * 100) if delta > 0 else 100
    veredicto = "ÓPTIMA" if integridad > 98 else "ACEPTABLE" if integridad > 90 else "CRÍTICA"

    bar('╔', '═', '╗')
    row("💓 ESTUDIO DE " + ("HOY" if args.periodo=="hoy" else "SEMANA" if args.periodo=="semana" else "TOTAL") + ":")
    if args.periodo == "hoy":
        row("   " + get_esp_day(f_ini) + " " + f_ini.strftime("%d/%m"))
    elif args.periodo == "semana":
        row("   " + f_ini.strftime("%d/%m") + " -> " + f_fin.strftime("%d/%m"))
    else:
        row("   " + f_ini.strftime("%d/%m/%y") + " -> " + f_fin.strftime("%d/%m/%y"))
    
    bar('╠', '═', '╣')
    row(f": {integridad:.1f}% INTEGRIDAD ({veredicto})")
    row(f"RESULTADO: {dur_b(tot_s)} PERDIDOS")
    bar('╠', '═', '╣')
    
    w_cat = [18, 10, 12]
    table_row(["CAT.", "CONTEO", "%"], w_cat)
    table_sep(w_cat)
    cats_f = ["1 min", "2 min", "3 min", "10 min", "15 min", "30 min", "El resto"]
    cnts = {c: 0 for c in cats_f}
    for r in rows: cnts[get_cat_name(r['latido'])[1]] += 1
    for c in cats_f:
        p = (cnts[c] / len(rows) * 100) if len(rows) > 0 else 0
        table_row([c, cnts[c], f"{p:.1f}%"], w_cat)
    
    if rows:
        bar('╠', '═', '╣')
        # Matemática: 5+8+8+6+7 = 34. + 12 (seps) = 46. + 4 (bordes) = 50.
        w_det = [5, 8, 8, 6, 7]
        table_row(["FECHA", "INICIO", "FIN", "DURAC.", "TIPO"], w_det)
        table_sep(w_det)
        for r in rows:
            t_f = datetime.fromisoformat(r['timestamp'])
            t_i = datetime.fromisoformat(r['hora_inicio'])
            tipo = get_cat_name(r['latido'])[0]
            table_row([t_f.strftime("%d/%m"), t_i.strftime("%H:%M:%S"), t_f.strftime("%H:%M:%S"), dur_b(r['latido']), tipo], w_det)
    
    bar('╚', '═', '╝')
    print("")

if __name__ == "__main__":
    main()
