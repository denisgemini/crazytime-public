"""
main.py - Servicio persistente CrazyTime v2.0

Ejecuta bucle infinito consultando API cada 3 minutos.
Diseñado para correr 24/7 en instancia GCP free tier.
"""

import sys
import time
import signal
import logging
from datetime import datetime

from orchestration.scheduler import CrazyTimeScheduler, setup_logging

shutdown_flag = False

def signal_handler(signum, frame):
    global shutdown_flag
    logger = logging.getLogger(__name__)
    logger.warning(f"\n⚠️ Señal recibida ({signum}), iniciando shutdown...")
    shutdown_flag = True

def main():
    global shutdown_flag
    setup_logging()
    logger = logging.getLogger(__name__)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    logger.info("\n" + "="*70)
    logger.info("🚀 CRAZYTIME SERVICE v2.0 - INICIANDO")
    logger.info("="*70)
    logger.info("Modo: Servicio persistente 24/7")
    logger.info("Intervalo: 3 minutos")
    logger.info("Plataforma: Google Cloud Platform Free Tier")
    logger.info("="*70 + "\n")
    try:
        scheduler = CrazyTimeScheduler()
        logger.info("✅ Scheduler inicializado correctamente")
    except Exception as e:
        logger.critical(f"💥 ERROR FATAL al inicializar: {e}", exc_info=True)
        sys.exit(1)
    try:
        if scheduler.notifier:
            scheduler.notifier.send_startup_notification()
    except Exception as e:
        logger.warning(f"No se pudo enviar notificación de inicio: {e}")
    cycle_count = 0
    while not shutdown_flag:
        cycle_count += 1
        try:
            logger.info(f"\n{'='*70}")
            logger.info(f"🔄 CICLO #{cycle_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"{'='*70}")
            scheduler.run()
            if not shutdown_flag:
                logger.info(f"\n⏳ Esperando 3 minutos hasta próximo ciclo...")
                for i in range(180):
                    if shutdown_flag:
                        break
                    time.sleep(1)
        except KeyboardInterrupt:
            logger.warning("\n⚠️ Interrupción por teclado detectada")
            shutdown_flag = True
        except Exception as e:
            logger.error(f"\n❌ ERROR EN CICLO #{cycle_count}: {e}", exc_info=True)
            try:
                if scheduler.notifier:
                    scheduler.notifier.send_error_notification(e, cycle_count)
            except:
                pass
            logger.info("⏳ Esperando 1 minuto antes de reintentar...")
            for i in range(60):
                if shutdown_flag:
                    break
                time.sleep(1)
    logger.info("\n" + "="*70)
    logger.info("🛑 APAGANDO SERVICIO")
    logger.info("="*70)
    try:
        if scheduler.notifier:
            scheduler.notifier.send_shutdown_notification(cycle_count)
    except:
        pass
    logger.info(f"✅ Servicio detenido limpiamente después de {cycle_count} ciclos")
    sys.exit(0)

if __name__ == "__main__":
    main()
