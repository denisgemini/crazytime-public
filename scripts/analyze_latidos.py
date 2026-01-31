"""
scripts/analyze_latidos.py - Reporte de Latidos Boxed (v4.10)
Definición de Salud Operativa: Rango 0-11s.
"""

import sqlite3
import os
import argparse
import unicodedata
from datetime import datetime, timedelta

DB_PATH = "data/db.sqlite3"
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
    l = max(0, needed // 2)
    r = max(0, needed - l)
    return (' ' * l) + text + (' ' * r)

def get_esp_day(dt):
    dias = ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", "SÁBADO", "DOMINGO"]
    return dias[dt.weekday()]

def bar(l='╔', m='═', r='╗'):
    print(f"{l}{m*(ANCHO_BOX-2)}{r}")

def row(text, align='left'):
    print(f"║ {pad_l(text, 46, align)} ║")

def table_sep(widths, l='╟', m='┼', r='╢', char='─'):
    parts = [char * (w + 2) for w in widths]
    linea = f"{l}{m.join(parts)}{r}"
    if len(linea) < ANCHO_BOX: 
        linea = linea[:-1] + char*(ANCHO_BOX-len(linea)) + r
    print(linea[:ANCHO_BOX])

def table_row(cells, widths, total_ref):
    items = []
    # Celda 1: Nombre (Left)
    items.append(pad_l(str(cells[0]), widths[0], 'left'))
    # Celda 2: Conteo (Right)
    items.append(pad_l(str(cells[1]), widths[1], 'right'))
    # Celda 3: % (Right)
    p = (cells[1] / total_ref * 100) if total_ref > 0 else 0
    items.append(pad_l(f"{p:.1f}%", widths[2], 'right'))
    print(f"║ {pad_l(' │ '.join(items), 46, 'left')} ║")

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
        cur.execute("SELECT latido FROM tiros WHERE timestamp >= ?", (f_ini.isoformat(),))
        lat = [r['latido'] for r in cur.fetchall()]
        conn.close()
        return lat, f_ini, now
    except: return [], None, None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--periodo", type=str, default="hoy")
    args = parser.parse_args()
    lat, f_ini, f_fin = obtener_datos(args.periodo)
    if not f_ini: return

    s = {"acel": 0, "est": 0, "len": 0, "gap": 0, "neg": 0, "tot": len(lat)}
    for l in lat:
        if l < 0: s["neg"] += 1
        elif 0 <= l <= 4: s["acel"] += 1
        elif l == 5: s["est"] += 1
        elif 6 <= l <= 11: s["len"] += 1
        else: s["gap"] += 1
    
    # SALUD OPERATIVA = Rango 0 a 11 segundos
    exitosos = s["acel"] + s["est"] + s["len"]
    total_real = s["tot"]
    estabilidad = (exitosos / total_real * 100) if total_real > 0 else 0
    veredicto = "ÓPTIMA" if estabilidad > 98 else "ESTABLE" if estabilidad > 90 else "INESTABLE"

    print("")
    bar('╔', '═', '╗')
    t = f"💓 ESTUDIO DE LATIDOS: {get_esp_day(f_ini)} {f_ini.strftime('%d/%m')}"
    if args.periodo == "semana": t = f"💓 ESTUDIO SEMANAL: {f_ini.strftime('%d/%m')} -> {f_fin.strftime('%d/%m')}"
    if args.periodo == "total": t = f"💓 ESTUDIO TOTAL: {f_ini.strftime('%d/%m/%y')} -> {f_fin.strftime('%d/%m/%y')}"
    row(t)
    
    bar('╠', '═', '╣')
    row(f"ESTADO : {estabilidad:.1f}% SALUDABLE ({veredicto})")
    bar('╠', '═', '╣')
    row(f"SALUD  : {total_real} tiros analizados | {s['neg']} anomalías")
    bar('╠', '═', '╣')
    
    w_cat = [18, 10, 12]
    print(f"║ {pad_l('CAT.', 18)} │ {pad_l('CONTEO', 10, 'right')} │ {pad_l('%', 12, 'right')} ║")
    table_sep(w_cat)
    
    table_row(["Aceler.ado", s["acel"]], w_cat, total_real)
    table_row(["Estable.", s["est"]], w_cat, total_real)
    table_row(["Lento.", s["len"]], w_cat, total_real)
    table_row(["Gaps.", s["gap"]], w_cat, total_real)
    table_row(["Negativos", s["neg"]], w_cat, total_real)
    
    bar('╚', '═', '╝')
    print("")

if __name__ == "__main__":
    main()