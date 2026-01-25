#!/usr/bin/env python3
"""
scripts/force_recalibration.py - Recalibración manual del tracker.

USO:
    python scripts/force_recalibration.py [--pattern PATTERN_ID]

DESCRIPCIÓN:
    Resetea el estado del tracker para uno o todos los patrones.
    Útil para forzar una recalibración manual del sistema.

OPTIONS:
    --pattern PATTERN_ID    Solo recalibrar un patrón específico
                            (ej: --pattern pachinko, --pattern crazytime)
"""

import os
import sys
import json
import argparse
from pathlib import Path

# Añadir el directorio padre al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

from analytics.pattern_tracker import PatternTracker
from config.patterns import ALL_PATTERNS


def force_recalibration(pattern_id: str = None):
    """
    Ejecuta recalibración del tracker.

    Args:
        pattern_id: Si se especifica, solo recalibra ese patrón.
                   Si es None, recalibra todos.
    """
    db_path = "data/db.sqlite3"
    state_file = "data/.tracker_state.json"

    if not os.path.exists(db_path):
        print(f"❌ Error: Base de datos no encontrada en {db_path}")
        return False

    # Cargar estado actual
    if os.path.exists(state_file):
        try:
            with open(state_file, "r") as f:
                state = json.load(f)
        except Exception as e:
            print(f"❌ Error cargando estado: {e}")
            return False
    else:
        print(f"⚠️ No existe archivo de estado en {state_file}")
        print("   El tracker se inicializará desde cero.")
        state = {
            "last_processed_id": 0,
            "last_result": None,
            "pattern_states": {
                pattern.id: {"last_id": None, "occurrences_count": 0}
                for pattern in ALL_PATTERNS
            }
        }

    # Recalibrar
    if pattern_id:
        # Recalibrar solo un patrón
        if pattern_id not in state["pattern_states"]:
            print(f"❌ Error: Patrón '{pattern_id}' no encontrado")
            print(f"   Patrones disponibles: {', '.join(state['pattern_states'].keys())}")
            return False

        print(f"🔄 Recalibrando patrón: {pattern_id}")
        state["pattern_states"][pattern_id]["last_id"] = None
        state["pattern_states"][pattern_id]["occurrences_count"] = 0
        print(f"✅ Patrón '{pattern_id}' recalibrado")
    else:
        # Recalibrar todos
        print(f"🔄 Recalibrando todos los patrones...")
        for pattern_id in state["pattern_states"]:
            state["pattern_states"][pattern_id]["last_id"] = None
            state["pattern_states"][pattern_id]["occurrences_count"] = 0
        state["last_result"] = None
        print(f"✅ Todos los patrones recalibrados")

    # Guardar estado
    try:
        os.makedirs(os.path.dirname(state_file), exist_ok=True)
        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)
        print(f"💾 Estado guardado en {state_file}")
        return True
    except Exception as e:
        print(f"❌ Error guardando estado: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Recalibración manual del tracker de patrones",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--pattern",
        type=str,
        help="ID del patrón a recalibrar (ej: pachinko, crazytime)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Listar patrones disponibles"
    )

    args = parser.parse_args()

    if args.list:
        print("📋 Patrones disponibles:")
        print("-" * 50)
        for pattern in ALL_PATTERNS:
            print(f"  {pattern.id:20s} - {pattern.name}")
        return

    success = force_recalibration(args.pattern)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
