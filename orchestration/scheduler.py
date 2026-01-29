"""
orchestration/scheduler.py - Orquestador principal del sistema.
"""

import os
import logging
import time
from datetime import datetime, timedelta
from typing import Optional

from dotenv import load_dotenv

from core.collector import DataCollector
from core.database import Database
from analytics.pattern_tracker import PatternTracker
from alerting.alert_manager import AlertManager
from alerting.notification import TelegramNotifier

logger = logging.getLogger(__name__)

class CrazyTimeScheduler:
    """Orquestador del sistema CrazyTime."""

    def __init__(self):
        load_dotenv()
        self.db = Database("data/db.sqlite3")
        self.collector = DataCollector("data/db.sqlite3")
        self.tracker = PatternTracker("data/db.sqlite3")
        self.alert_manager = AlertManager("data/db.sqlite3")
        token = os.getenv("TELEGRAM_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if not token or not chat_id:
            logger.warning("⚠️ Credenciales de Telegram no configuradas")
            self.notifier = None
        else:
            self.notifier = TelegramNotifier(token, chat_id)
        # self.daily_summary_file = "data/.last_summary" <-- DEPRECATED
        self.backup_control_file = "data/backups/.last_backup"
        # self.last_run_file = "data/.scheduler_last_run" <-- DEPRECATED

    def run(self):
        try:
            logger.info("=" * 70)
            logger.info("🚀 INICIANDO CICLO DE ACTUALIZACIÓN")
            logger.info("=" * 70)

            # Actualizar datos
            new_spins = self._update_data()
            if new_spins == 0:
                logger.info("✅ No hay datos nuevos, ciclo completado")
                self._update_last_run()
                return

            self._process_tracking()
            self._process_alerts()

            # Análisis de ventanas
            self._run_window_analysis()
            self._scheduled_tasks()

            self._update_last_run()

            logger.info("=" * 70)
            logger.info("✅ CICLO COMPLETADO EXITOSAMENTE")
            logger.info("=" * 70)
        except Exception as e:
            logger.error(f"❌ ERROR CRÍTICO EN CICLO: {e}", exc_info=True)
            self._send_error_alert(e)

    def _update_last_run(self):
        """Registra timestamp de última ejecución en BD"""
        self.db.set_state("scheduler", "last_run", datetime.now().isoformat())

    def _update_data(self) -> int:
        try:
            logger.info("📡 Consultando API...")
            new_count = self.collector.fetch_and_store()
            return new_count
        except Exception as e:
            logger.error(f"❌ Error actualizando datos: {e}", exc_info=True)
            return 0

    def _process_tracking(self):
        try:
            logger.info("📊 Procesando tracking de distancias...")
            processed = self.tracker.process_new_spins()
            if processed > 0:
                logger.info(f"✅ Tracking: {processed} tiros procesados")
                from config.patterns import VIP_PATTERNS
                for pattern in VIP_PATTERNS:
                    stats = self.tracker.get_pattern_statistics(pattern.id)
                    if stats:
                        logger.info(f"   📈 {pattern.name}: Media={stats.get('mean', 0):.1f}, Mediana={stats.get('median', 0)}, Total={stats.get('count', 0)}")
        except Exception as e:
            logger.error(f"❌ Error en tracking: {e}", exc_info=True)

    def _process_alerts(self):
        try:
            logger.info("🚨 Evaluando alertas...")
            alerts = self.alert_manager.check_all_patterns()
            if not alerts:
                logger.info("✅ Sin alertas que enviar")
                return
            logger.info(f"📤 {len(alerts)} alertas detectadas")
            if not self.notifier:
                logger.warning("⚠️ Notificador no disponible, alertas no enviadas")
                return
            for alert in alerts:
                try:
                    self.notifier.send_alert(alert)
                    logger.info(f"✅ Alerta enviada: {alert.pattern_name} ({alert.type.value})")
                except Exception as e:
                    logger.error(f"Error enviando alerta: {e}")
        except Exception as e:
            logger.error(f"❌ Error procesando alertas: {e}", exc_info=True)

    def _run_window_analysis(self):
        """
        Ejecuta análisis de ventanas si hay datos suficientes.

        Criterio: Al menos 10 apariciones de algún patrón VIP.
        """
        try:
            from analytics.window_analyzer import WindowAnalyzer
            from config.patterns import VIP_PATTERNS

            # Verificar si hay suficientes datos
            should_analyze = False

            for pattern in VIP_PATTERNS:
                stats = self.tracker.get_pattern_statistics(pattern.id)
                count = stats.get('count', 0)

                if count >= 10:
                    should_analyze = True
                    logger.debug(f"📊 {pattern.name}: {count} apariciones (suficiente para análisis)")
                    break

            if not should_analyze:
                logger.debug("📊 Analytics: Datos insuficientes (<10 apariciones)")
                return

            logger.info("📊 Ejecutando análisis de ventanas...")

            analyzer = WindowAnalyzer('data/db.sqlite3')
            results = analyzer.analyze_all_patterns()

            # Log de resultados
            for pattern_id, data in results.items():
                pattern_name = data.get('pattern_name', pattern_id)
                windows = data.get('windows', {})

                for window_range, metrics in windows.items():
                    roi = metrics.get('roi', 0)
                    win_rate = metrics.get('win_rate', 0)
                    logger.info(
                        f"   📈 {pattern_name} (Ventana {window_range}): "
                        f"ROI={roi:+.1f}%, Win Rate={win_rate:.1f}%"
                    )

            logger.info("✅ Análisis de ventanas completado")

        except Exception as e:
            logger.error(f"❌ Error en análisis de ventanas: {e}", exc_info=True)

    def _scheduled_tasks(self):
        try:
            if self._should_send_daily_summary():
                self._send_daily_summary()
            if self._should_run_backup():
                self._run_backup()
        except Exception as e:
            logger.error(f"❌ Error en tareas programadas: {e}")

    def _should_send_daily_summary(self) -> bool:
        try:
            now = datetime.now()  # FIXED: Server already in America/Lima timezone
            hour = now.hour
            minute = now.minute
            today = now.strftime("%Y-%m-%d")
            # Reporte de cierre de jornada a las 23:24
            if not (hour == 23 and minute >= 24):
                return False
            
            # Verificar estado en BD
            last_date = self.db.get_state("scheduler", "last_summary_date")
            
            # Migración fallback (si existe archivo viejo y no hay dato en BD)
            legacy_file = "data/.last_summary"
            if not last_date and os.path.exists(legacy_file):
                with open(legacy_file, "r") as f:
                    last_date = f.read().strip()
                self.db.set_state("scheduler", "last_summary_date", last_date)

            if last_date == today:
                return False
            return True
        except Exception as e:
            logger.error(f"Error verificando resumen diario: {e}")
            return False

    def _send_daily_summary(self):
        try:
            logger.info("📊 Generando resumen diario estratégico...")
            
            # Delegar lógica al generador especializado
            from analytics.daily_report import DailyReportGenerator
            generator = DailyReportGenerator("data/db.sqlite3")
            full_report = generator.generate()

            if not full_report:
                logger.info("ℹ️ Sin datos suficientes para resumen diario")
                return

            if self.notifier:
                self.notifier.enviar_resumen_diario(full_report)
                today = datetime.now().strftime("%Y-%m-%d")
                # Guardar estado en BD
                self.db.set_state("scheduler", "last_summary_date", today)
                logger.info("✅ Resumen diario estratégico enviado")

        except Exception as e:
            logger.error(f"❌ Error enviando resumen diario: {e}", exc_info=True)

    def _should_run_backup(self) -> bool:
        try:
            if not os.path.exists(self.backup_control_file):
                return True
            last_backup = os.path.getmtime(self.backup_control_file)
            hours_since = (time.time() - last_backup) / 3600
            return hours_since >= 24
        except Exception as e:
            logger.error(f"Error verificando backup: {e}")
            return False

    def _run_backup(self):
        try:
            logger.info("💾 Ejecutando backup automático...")
            from scripts.auto_backup import ejecutar_backup_si_necesario
            ejecutar_backup_si_necesario(
                db_path="data/db.sqlite3",
                backup_dir="data/backups",
                notifier=self.notifier
            )
            logger.info("✅ Backup completado")
        except Exception as e:
            logger.error(f"❌ Error en backup: {e}")

    def _send_error_alert(self, error: Exception):
        try:
            if self.notifier:
                self.notifier.send_message(
                    f"🚨 <b>ERROR CRÍTICO EN SISTEMA</b>\n\n"
                    f"<code>{type(error).__name__}: {str(error)}</code>\n\n"
                    f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"Revisar logs del sistema"
                )
        except:
            pass


def setup_logging():
    """Configura sistema de logging."""
    os.makedirs("data/logs", exist_ok=True)
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(
        "data/logs/system.log",
        maxBytes=10*1024*1024,
        backupCount=30,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(levelname)s - %(message)s")
    console_handler.setFormatter(console_formatter)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
