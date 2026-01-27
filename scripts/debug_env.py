
import sys
import os

print(f"Python Executable: {sys.executable}")
print(f"Python Version: {sys.version}")
print("\nSys Path (donde busca librerías):")
for path in sys.path:
    print(f" - {path}")

try:
    import openpyxl
    print(f"\n✅ openpyxl detectado en: {openpyxl.__file__}")
except ImportError:
    print("\n❌ openpyxl NO detectado")
