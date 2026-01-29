"""
alerting/notification.py - Notificador de Telegram con soporte de imágenes.
"""

import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional

from telegram import Bot
from telegram.error import TelegramError

from alerting.alert_manager import Alert, AlertType
from config.patterns import get_pattern_image, get_window_range

logger = logging.getLogger(__name__)

class TelegramNotifier:
    """Notificador de Telegram con soporte de imágenes."""

    def __init__(self, token: str, chat_id: str, assets_dir: str = "assets"):
        self.token = token
        self.chat_id = chat_id
        self.bot = Bot(token=self.token)
        self.assets_dir = assets_dir
        logger.info("✅ Bot de Telegram inicializado")

    def send_alert(self, alert: Alert) -> bool:
        if alert.type == AlertType.THRESHOLD_REACHED:
            return self.send_threshold_alert(alert)
        elif alert.type == AlertType.PATTERN_HIT:
            return self.send_hit_alert(alert)
        else:
            logger.error(f"Tipo de alerta desconocido: {alert.type}")
            return False

    def _get_image_path(self, pattern_id: str) -> Optional[str]:
        """Obtiene la ruta de la imagen para un patrón."""
        filename = get_pattern_image(pattern_id)
        if not filename:
            return None
        full_path = os.path.join(self.assets_dir, filename)
        if os.path.exists(full_path):
            return full_path
        return None

    def send_threshold_alert(self, alert: Alert) -> bool:
        window_start, window_end = get_window_range(alert.threshold)
        hora = alert.timestamp.strftime("%H:%M:%S")
        mensaje = f"""🟡 <b>UMBRAL ALCANZADO</b>

📊 <b>Patrón:</b> {alert.pattern_name}
⏱️ <b>Tiros sin salir:</b> {alert.spin_count}
🎯 <b>Umbral:</b> {alert.threshold}

📍 <b>Ventana de apuesta:</b> tiros {window_start}-{window_end}
🕐 <b>Hora:</b> {hora}
"""
        imagen = self._get_image_path(alert.pattern_id)
        return self.send_message(mensaje.strip(), imagen_path=imagen)

    def send_hit_alert(self, alert: Alert) -> bool:
        details = alert.details
        hora_juego = details.get("timestamp", "")
        if "T" in hora_juego:
            hora_juego = hora_juego.split("T")[1][:8]
        mensaje = f"""🎉 <b>SALIÓ {alert.pattern_name.upper()}</b>

⏱️ <b>Salió después de:</b> {alert.spin_count} tiros
🎯 <b>Umbral era:</b> {alert.threshold}
"""
        if alert.pattern_id == "pachinko":
            bonus = details.get("bonus_multiplier", "?")
            mensaje += f"💰 <b>Pago:</b> {bonus}x\n"
            if details.get("top_slot_matched"):
                ts = details.get("top_slot_multiplier", 1)
                total = bonus * ts if bonus != "?" else "?"
                mensaje += f"🎁 <b>Top Slot Match:</b> x{ts} ({total}x total)\n"
        elif alert.pattern_id == "crazytime":
            blue = details.get("flapper_blue", "?")
            green = details.get("flapper_green", "?")
            yellow = details.get("flapper_yellow", "?")
            mensaje += f"🔵 <b>Flapper Azul:</b> {blue}x\n"
            mensaje += f"🟢 <b>Flapper Verde:</b> {green}x\n"
            mensaje += f"🟡 <b>Flapper Amarillo:</b> {yellow}x\n"
            if details.get("top_slot_matched"):
                ts = details.get("top_slot_multiplier", 1)
                mensaje += f"🎁 <b>Top Slot Match:</b> x{ts}\n"
        mensaje += f"\n🕐 <b>Hora:</b> {hora_juego}\n"
        imagen = self._get_image_path(alert.pattern_id)
        return self.send_message(mensaje.strip(), imagen_path=imagen)

    def send_message(self, mensaje: str, imagen_path: str = None, parse_mode: str = "HTML") -> bool:
        try:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._send_message_async(mensaje, parse_mode, imagen_path))
            return result
        except Exception as e:
            logger.error(f"❌ Error en wrapper síncrono: {e}")
            return False

    async def _send_message_async(self, mensaje: str, parse_mode: str, imagen_path: str = None) -> bool:
        try:
            if imagen_path and os.path.exists(imagen_path):
                with open(imagen_path, "rb") as f:
                    await self.bot.send_photo(
                        chat_id=self.chat_id,
                        photo=f,
                        caption=mensaje,
                        parse_mode=parse_mode
                    )
                logger.info(f"📤 Foto enviada a Telegram: {imagen_path}")
            else:
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=mensaje,
                    parse_mode=parse_mode
                )
                logger.info(f"📤 Mensaje enviado a Telegram")
            return True
        except TelegramError as e:
            logger.error(f"❌ Error de Telegram: {e}")
            return False

    def enviar_resumen_diario(self, estadisticas: dict) -> bool:
        try:
            fecha = datetime.now().strftime("%Y-%m-%d")
            total = estadisticas.get("total_spins", 0)
            if total == 0:
                return False
            num_1 = estadisticas.get("1", 0)
            num_2 = estadisticas.get("2", 0)
            num_5 = estadisticas.get("5", 0)
            pct_1 = (num_1 / total * 100) if total > 0 else 0
            pct_2 = (num_2 / total * 100) if total > 0 else 0
            pct_5 = (num_5 / total * 100) if total > 0 else 0
            mensaje = f"""📊 <b>RESUMEN DIARIO - CRAZYTIME</b>

📅 <b>Fecha:</b> {fecha}
🔢 <b>Total de spins:</b> {total}

<b>🎲 NÚMEROS BÁSICOS:</b>
• 1: {num_1} veces ({pct_1:.1f}%)
• 2: {num_2} veces ({pct_2:.1f}%)
• 5: {num_5} veces ({pct_5:.1f}%)
• 10: {estadisticas.get("10", 0)} veces

<b>🎰 BONUS ROUNDS:</b>
• Coin Flip: {estadisticas.get("CoinFlip", 0)} veces
• Cash Hunt: {estadisticas.get("CashHunt", 0)} veces
• Pachinko: {estadisticas.get("Pachinko", 0)} veces
• Crazy Time: {estadisticas.get("CrazyTime", 0)} veces
"""
            return self.send_message(mensaje.strip())
        except Exception as e:
            logger.error(f"❌ Error enviando resumen diario: {e}")
            return False

    def test_conexion(self) -> bool:
        mensaje = """✅ <b>CRAZYTIME BOT v2.0 ACTIVO</b>

Conexión establecida correctamente.
Sistema rediseñado con alertas optimizadas y soporte de imágenes 📸
"""
        return self.send_message(mensaje.strip())

    def send_startup_notification(self) -> bool:
        mensaje = """🚀 <b>SERVICIO INICIADO</b>

CrazyTime Analytics v2.0
Modo: 24/7 persistente
"""
        return self.send_message(mensaje.strip())

    def send_shutdown_notification(self, cycle_count: int) -> bool:
        mensaje = f"""🛑 <b>SERVICIO DETENIDO</b>

Ciclos ejecutados: {cycle_count}
"""
        return self.send_message(mensaje.strip())

    def send_error_notification(self, error: Exception, cycle_num: int) -> bool:
        mensaje = f"""🚨 <b>ERROR EN CICLO #{cycle_num}</b>

<code>{type(error).__name__}: {str(error)}</code>

El servicio continúa ejecutándose...
"""
        return self.send_message(mensaje.strip())
