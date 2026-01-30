#!/usr/bin/env python3
"""
Fix para scheduler.py - Elimina llamadas a get_pattern_statistics() que no existe
"""

# Leer el archivo
with open('orchestration/scheduler.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Buscar y eliminar las líneas problemáticas
new_lines = []
skip_until = -1

for i, line in enumerate(lines):
    # Si estamos en modo "skip", saltamos hasta la línea indicada
    if i < skip_until:
        continue
    
    # FIX 1: Detectar inicio del bloque problemático en _process_tracking
    if 'from config.patterns import VIP_PATTERNS' in line and i > 100 and i < 110:
        # Saltar las siguientes 4 líneas (el for loop completo)
        skip_until = i + 5
        continue
    
    # FIX 2: Detectar get_pattern_statistics en _run_window_analysis
    if 'stats = self.tracker.get_pattern_statistics(pattern.id)' in line:
        # Reemplazar con get_pattern_state
        new_lines.append(line.replace(
            'stats = self.tracker.get_pattern_statistics(pattern.id)',
            'state = self.tracker.get_pattern_state(pattern.id)'
        ))
        continue
    
    if "count = stats.get('count', 0)" in line:
        # Reemplazar la lógica de conteo
        indent = len(line) - len(line.lstrip())
        new_lines.append(' ' * indent + 'count = state.get("prev_distance", 0) if state.get("last_id") else 0\n')
        continue
    
    new_lines.append(line)

# Escribir el archivo corregido
with open('orchestration/scheduler.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✅ scheduler.py corregido exitosamente")
