"""
scripts/auto_backup.py - Sistema de backups automáticos.
"""

import os
import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def ejecutar_backup_si_necesario(db_path: str, backup_dir: str, notifier=None) -> bool:
    try:
        os.makedirs(backup_dir, exist_ok=True)
        control_file = os.path.join(backup_dir, ".last_backup")
        if os.path.exists(control_file):
            last_backup = os.path.getmtime(control_file)
            hours_since = (datetime.now().timestamp() - last_backup) / 3600
            if hours_since < 24:
                logger.debug(f"Backup no necesario (hace {hours_since:.1f}h)")
                return False
        logger.info("💾 Iniciando backup automático...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"backup_{timestamp}.db")
        source_conn = sqlite3.connect(db_path, timeout=20)
        backup_conn = sqlite3.connect(backup_file)
        source_conn.backup(backup_conn)
        backup_conn.close()
        source_conn.close()
        size_mb = os.path.getsize(backup_file) / (1024 * 1024)
        logger.info(f"✅ Backup creado: {backup_file} ({size_mb:.2f} MB)")
        aplicar_politica_retencion(backup_dir)
        with open(control_file, "w") as f:
            f.write(datetime.now().isoformat())
        return True
    except Exception as e:
        logger.error(f"❌ Error en backup: {e}", exc_info=True)
        if notifier:
            try:
                notifier.send_message(
                    f"⚠️ <b>ERROR EN BACKUP</b>\n\n"
                    f"Error: {str(e)}\n"
                    f"Hora: {datetime.now().strftime('%H:%M:%S')}"
                )
            except:
                pass
        return False

def aplicar_politica_retencion(backup_dir: str):
    try:
        backups = [f for f in os.listdir(backup_dir) if f.startswith("backup_") and f.endswith(".db")]
        if not backups:
            return
        backups.sort(reverse=True)
        backup_dates = []
        for backup in backups:
            try:
                date_str = backup.split("_")[1]
                date = datetime.strptime(date_str, "%Y%m%d")
                backup_dates.append((backup, date))
            except:
                continue
        keep = set()
        now = datetime.now()
        for i in range(7):
            target_date = (now - timedelta(days=i)).date()
            for backup, date in backup_dates:
                if date.date() == target_date:
                    keep.add(backup)
                    break
        for i in range(4):
            target_week_start = now - timedelta(weeks=i)
            days_to_sunday = (target_week_start.weekday() + 1) % 7
            sunday = target_week_start - timedelta(days=days_to_sunday)
            for backup, date in backup_dates:
                if date.date() == sunday.date():
                    keep.add(backup)
                    break
        for i in range(3):
            target_month = now.month - i
            target_year = now.year
            while target_month <= 0:
                target_month += 12
                target_year -= 1
            first_day = datetime(target_year, target_month, 1).date()
            for backup, date in backup_dates:
                if date.date() == first_day:
                    keep.add(backup)
                    break
        deleted = 0
        for backup in backups:
            if backup not in keep:
                filepath = os.path.join(backup_dir, backup)
                os.remove(filepath)
                deleted += 1
        if deleted > 0:
            logger.info(f"🧹 Política 7-4-3 aplicada: {deleted} backups eliminados")
        logger.info(f"💾 Backups retenidos: {len(keep)}")
    except Exception as e:
        logger.error(f"Error aplicando política de retención: {e}")

from datetime import timedelta
