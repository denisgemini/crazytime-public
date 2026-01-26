import sys
from pathlib import Path
import sqlite3
import json

# Simular la lógica de rutas de app.py
BASE_DIR = Path(__file__).resolve().parent
BASE_DATA_PATH = Path(BASE_DIR.parent / "data")
DB_PATH = BASE_DATA_PATH / "db.sqlite3"
TRACKER_STATE_PATH = BASE_DATA_PATH / ".tracker_state.json"

print(f"--- DIAGNÓSTICO DE RUTAS ---")
print(f"Directorio Base (dashboard): {BASE_DIR}")
print(f"Directorio de Datos esperado: {BASE_DATA_PATH}")
print(f"Ruta DB esperada: {DB_PATH}")

print(f"\n--- VERIFICACIÓN DE ARCHIVOS ---")
if DB_PATH.exists():
    print(f"✅ Base de datos ENCONTRADA en: {DB_PATH}")
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tiros")
        count = cursor.fetchone()[0]
        print(f"✅ Conexión exitosa. Tiros en DB: {count}")
        
        cursor.execute("SELECT id, resultado, timestamp FROM tiros ORDER BY id DESC LIMIT 1")
        last = cursor.fetchone()
        print(f"ℹ️ Último tiro: {last}")
        conn.close()
    except Exception as e:
        print(f"❌ ERROR al leer la DB: {e}")
else:
    print(f"❌ Base de datos NO ENCONTRADA en {DB_PATH}")

if TRACKER_STATE_PATH.exists():
    print(f"✅ Tracker State ENCONTRADO en: {TRACKER_STATE_PATH}")
    try:
        with open(TRACKER_STATE_PATH, 'r') as f:
            data = json.load(f)
            print(f"ℹ️ Último ID procesado: {data.get('last_processed_id', 'N/A')}")
    except:
        print("❌ Error leyendo Tracker State")
else:
    print(f"❌ Tracker State NO ENCONTRADO en {TRACKER_STATE_PATH}")
