"""
scripts/analyze_recuperacion.py - Reporte de Recuperación Boxed
Soporte Multi-Lote: Suma inteligente de inyecciones parciales.
"""

import os
import glob
import argparse
import unicodedata
from datetime import datetime, timedelta

LOG_PATTERN = "data/logs/system.log*"
ANCHO_BOX = 60  # Aumentado para caber la columna Lotes

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
    print(f"║ {pad_l(text, ANCHO_BOX-4, align)} ║")

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
    print(f"║ {pad_l(contenido, ANCHO_BOX-4, 'left')} ║")

def parse_logs(f_ini):
    escaleras, vacios, bloqueos = [], [], []
    exitos, fallos = 0, 0
    
    # Lectura de logs (El más nuevo al más viejo a nivel archivo, pero lectura interna secuencial)
    files = sorted(glob.glob(LOG_PATTERN), reverse=True) 
    
    # Invertimos la lista de archivos para leer del más antiguo al más nuevo y mantener el estado
    files = sorted(files) 
    
    curr_esc = None # Estado del evento actual

    for f_path in files:
        try:
            with open(f_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    try:
                        parts = line.split(' - ')
                        if len(parts) < 4: continue
                        
                        ts_str = parts[0].split(',')[0]
                        ts = datetime.fromisoformat(ts_str)
                        if ts < f_ini: continue # Ignorar datos viejos
                        
                        msg = parts[3].strip()
                        h = ts.strftime("%H:%M:%S")

                        # 1. INICIO DE EVENTO (BRECHA)
                        if "🚨 BRECHA DETECTADA" in msg:
                            # Si había uno abierto sin cerrar (raro), lo cerramos como parcial
                            if curr_esc: 
                                escaleras.append(curr_esc)
                            
                            gap_val = msg.split(': ')[1].split('.')[0]+"s"
                            curr_esc = {
                                "h": h, 
                                "gap": gap_val, 
                                "p": "??", 
                                "iny_count": 0, 
                                "lotes": 1,
                                "st": "PENDING"
                            }

                        # 2. DETALLE DE PÁGINA
                        elif "✅ Empalme hallado en Page" in msg:
                            if curr_esc: 
                                curr_esc["p"] = "P"+msg.split("Page ")[1]

                        # 3. DETALLE DE LOTES (Multi-lote)
                        elif "Procesando lote de recuperación" in msg:
                            # Formato: ... recuperación X/Y...
                            if curr_esc:
                                try:
                                    partes_lote = msg.split("recuperación ")[1].split("/")[1]
                                    curr_esc["lotes"] = partes_lote.split(".")[0] # Total lotes
                                except: pass

                        # 4. SUMA DE TIROS (Acumulativo)
                        elif "✅ Tracking:" in msg:
                            if curr_esc:
                                try:
                                    num = int(msg.split(": ")[1].split(" ")[0])
                                    curr_esc["iny_count"] += num
                                except: pass

                        # 5. CIERRE EXITOSO (Nuevo log explícito)
                        elif "✅ RECUPERACIÓN EXITOSA" in msg:
                            if curr_esc:
                                try:
                                    # ... total de X tiros en Y lotes
                                    txt_tiros = msg.split("total de ")[1].split(" tiros")[0]
                                    txt_lotes = msg.split("en ")[1].split(" lotes")[0]
                                    curr_esc["iny_count"] = int(txt_tiros)
                                    curr_esc["lotes"] = txt_lotes
                                except: pass
                                
                                curr_esc["st"] = "ÉXITO"
                                escaleras.append(curr_esc)
                                exitos += 1
                                curr_esc = None

                        # 6. CIERRE GENÉRICO (Fin de ciclo normal)
                        elif "✅ CICLO COMPLETADO" in msg:
                            if curr_esc:
                                curr_esc["st"] = "ÉXITO"
                                escaleras.append(curr_esc)
                                exitos += 1
                                curr_esc = None

                        # 7. FALLO
                        elif "❌ No se encontró empalme" in msg:
                            if curr_esc:
                                curr_esc["st"] = "FALLO"
                                curr_esc["iny_count"] = 0
                                escaleras.append(curr_esc)
                                fallos += 1
                                curr_esc = None

                        # OTROS EVENTOS (Sin estado)
                        elif "✅ No hay datos nuevos" in msg:
                            vacios.append({"h": h, "m": "Sin datos"})
                        elif "❌ API: Fallo total" in msg:
                            vacios.append({"h": h, "m": "Error API"})
                        elif "⚠️ ANOMALÍA [Filtro 10s]" in msg:
                            res = msg.split(": ")[1].split(" (")[0]
                            choque = "ID #" + msg.split("ID #")[1].split(" ")[0]
                            bloqueos.append({"h": h, "c": choque, "r": res})

                    except Exception as e: continue
        except: pass

    return escaleras, vacios, bloqueos, exitos, fallos

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--periodo", type=str, default="hoy")
    args = parser.parse_args()
    
    now = datetime.now()
    if args.periodo == "hoy": 
        f_ini = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif args.periodo == "semana":
        f_ini = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    else: 
        f_ini = now - timedelta(days=365)

    es, va, bl, ok, err = parse_logs(f_ini)

    bar('╔', '═', '╗')
    t = f"🔄 REPORTE DE RECUPERACIÓN"
    row(t, 'center')
    row(f"Período: {f_ini.strftime('%d/%m %H:%M')} -> {now.strftime('%H:%M')}", 'center')
    
    # SECCIÓN 1: REENGANCHES
    bar('╠', '═', '╣')
    res_esc = f"{ok} ÉXITOS" if err == 0 else f"{ok} ÉXITOS / {err} FALLOS"
    row(f"🟢 EVENTOS DE RECUPERACIÓN: {res_esc}")
    
    # Definición de anchos: HORA(8), GAP(8), PAG(4), LOT(5), TIROS(8), EST(8)
    w_e = [8, 8, 4, 5, 8, 8]
    bar('╠', '═', '╣')
    table_row(["HORA", "GAP", "PAG", "LOTES", "TIROS", "ESTADO"], w_e)
    table_sep(w_e, '╟', '┼', '╢', '─')
    
    if not es: 
        row("No hay recuperaciones registradas.")
    else:
        for e in es: 
            table_row([
                e['h'], 
                e['gap'], 
                e['p'], 
                e['lotes'],
                f"+{e['iny_count']}", 
                e['st']
            ], w_e)

    # SECCIÓN 2: CICLOS VACÍOS
    bar('╠', '═', '╣')
    row("⚪ CICLOS SIN DATOS (0 TIROS):")
    w_v = [8, 30, 8]
    bar('╠', '═', '╣')
    table_row(["HORA", "MOTIVO", "TIROS"], w_v)
    table_sep(w_v, '╟', '┼', '╢', '─')
    if not va: row("No hay ciclos vacíos.")
    else:
        for v in va: table_row([v['h'], v['m'], "0"], w_v)

    # SECCIÓN 3: BLOQUEOS
    bar('╠', '═', '╣')
    row("🚫 BLOQUEOS (ANOMALÍAS ID):")
    w_b = [8, 12, 30]
    bar('╠', '═', '╣')
    table_row(["HORA", "CHOQUE", "RESULTADO"], w_b)
    table_sep(w_b, '╟', '┼', '╢', '─')
    if not bl: row("No hay bloqueos.")
    else:
        for b in bl: table_row([b['h'], b['c'], b['r']], w_b)

    bar('╚', '═', '╝')
    print("")

if __name__ == "__main__":
    main()