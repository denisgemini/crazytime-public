"""
scripts/analyze_recuperacion.py - Reporte de Recuperación Boxed (v4.9)
Diseño de Alta Precisión Sincronizado con Brechas (Sin Límites).
"""

import os
import glob
import argparse
import unicodedata
import sqlite3
from datetime import datetime, timedelta

DB_PATH = "data/db.sqlite3"
LOG_PATTERN = "data/logs/system.log*"
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

def table_row(cells, widths):
    items = []
    for i in range(len(cells)):
        items.append(pad_l(str(cells[i]), widths[i], 'left'))
    contenido = " │ ".join(items)
    print(f"║ {pad_l(contenido, 46, 'left')} ║")

def parse_logs(f_ini):
    escaleras, vacios, bloqueos = [], [], []
    exitos, fallos = 0, 0
    try:
        files = sorted(glob.glob(LOG_PATTERN), reverse=True)
        for f_path in files:
            with open(f_path, 'r', encoding='utf-8', errors='ignore') as f:
                curr_esc = None
                for line in f:
                    try:
                        parts = line.split(' - ')
                        if len(parts) < 4: continue
                        ts = datetime.fromisoformat(parts[0].split(',')[0])
                        if ts < f_ini: continue
                        msg = parts[3].strip()
                        h = ts.strftime("%H:%M:%S")
                        
                        if "🚨 BRECHA DETECTADA" in msg:
                            curr_esc = {"h": h, "gap": msg.split(': ')[1].split('.')[0]+"s", "p": "??", "iny": "0", "st": "ÉXITO"}
                        elif "✅ Empalme hallado en Page" in msg:
                            if curr_esc: curr_esc["p"] = "P"+msg.split("Page ")[1]
                        elif "❌ No se encontró empalme" in msg:
                            if curr_esc:
                                fallos += 1
                                curr_esc["st"] = "FALLO"
                                curr_esc["iny"] = "0"
                                escaleras.append(curr_esc); curr_esc = None
                        elif "✅ Tracking:" in msg:
                            if curr_esc:
                                exitos += 1
                                curr_esc["iny"] = msg.split(": ")[1].split(" ")[0]
                                escaleras.append(curr_esc); curr_esc = None
                        elif "✅ No hay datos nuevos" in msg:
                            vacios.append({"h": h, "m": "Sin datos"})
                        elif "❌ API: Fallo total" in msg:
                            vacios.append({"h": h, "m": "Error API"})
                        elif "⚠️ ANOMALÍA [Filtro 10s]" in msg:
                            res = msg.split(": ")[1].split(" (")[0]
                            choque = "ID #" + msg.split("ID #")[1].split(" ")[0]
                            bloqueos.append({"h": h, "c": choque, "r": res})
                    except: continue
    except: pass
    return escaleras, vacios, bloqueos, exitos, fallos

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--periodo", type=str, default="hoy")
    args = parser.parse_args()
    now = datetime.now()
    if args.periodo == "hoy": f_ini = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif args.periodo == "semana":
        f_ini = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    else: f_ini = now - timedelta(days=365)

    es, va, bl, ok, err = parse_logs(f_ini)

    bar('╔', '═', '╗')
    t = f"🔄 ESTUDIO DE RECUPERACIÓN: {get_esp_day(f_ini)} {f_ini.strftime('%d/%m')}"
    if args.periodo != "hoy": t = f"🔄 ESTUDIO SEMANAL: {f_ini.strftime('%d/%m')} -> {now.strftime('%d/%m')}"
    row(t)
    
    # SECCIÓN 1: REENGANCHES
    bar('╠', '═', '╣')
    res_esc = f"{ok} exitos" if err == 0 else f"{ok} / {err}"
    row(f"🟢 REENGANCHES (ESCALERAS): {res_esc}")
    w_e = [8, 8, 4, 7, 7]
    bar('╠', '═', '╣')
    table_row(["HORA", "GAP", "PAG", "INY.", "ESTADO"], w_e)
    table_sep(w_e, '╟', '┼', '╢', '─')
    if not es: row("No hay reenganches registrados.")
    else:
        for e in es: table_row([e['h'], e['gap'], e['p'], e['iny'], e['st']], w_e)

    # SECCIÓN 2: CICLOS VACÍOS
    bar('╠', '═', '╣')
    row("⚪ INTENTOS SIN DATOS (0 TIROS):")
    w_v = [8, 24, 8]
    bar('╠', '═', '╣')
    table_row(["HORA", "MOTIVO", "TIROS"], w_v)
    table_sep(w_v, '╟', '┼', '╢', '─')
    if not va: row("No hay ciclos vacíos registrados.")
    else:
        for v in va: table_row([v['h'], v['m'], "0"], w_v)

    # SECCIÓN 3: BLOQUEOS
    bar('╠', '═', '╣')
    row("🚫 DETALLE DE BLOQUEOS (ANOMALÍAS):")
    w_b = [8, 10, 22]
    bar('╠', '═', '╣')
    table_row(["HORA", "CHOQUE", "RESULTADO"], w_b)
    table_sep(w_b, '╟', '┼', '╢', '─')
    if not bl: row("No hay bloqueos registrados.")
    else:
        for b in bl: table_row([b['h'], b['c'], b['r']], w_b)

    bar('╚', '═', '╝')
    print("")

if __name__ == "__main__":
    main()
