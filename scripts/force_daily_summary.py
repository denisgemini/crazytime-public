"""
scripts/force_daily_summary.py - Fuerza el envío del Resumen Diario Estratégico.
"""
import sys
import os
import logging
from datetime import datetime

# Añadir directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestration.scheduler import CrazyTimeScheduler, setup_logging

def force_summary():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("🚀 Forzando envío de Resumen Diario Estratégico...")
    
    scheduler = CrazyTimeScheduler()
    
    if not scheduler.notifier:
        logger.error("❌ No hay notificador configurado (Telegram Token faltante?)")
        return

    # Llamamos directamente al método interno que genera y envía el reporte
    # OJO: Este método usa la lógica de "23:00 ayer a 23:00 hoy"
    try:
        scheduler._send_daily_summary()
        logger.info("✅ Proceso finalizado. Revisa tu Telegram.")
    except Exception as e:
        logger.error(f"❌ Error forzando resumen: {e}", exc_info=True)

if __name__ == "__main__":
    force_summary()
