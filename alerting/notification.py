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

    def enviar_resumen_diario(self, data: dict) -> bool:
        try:
            # 1. Cabecera Festiva
            now = datetime.now()
            semana = now.strftime("%U")
            dias_es = ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", "SÁBADO", "DOMINGO"]
            dia_semana = dias_es[now.weekday()]
            
            start_str = data.get("range_start", "").replace("T", " ")[:16]
            end_str = data.get("range_end", "").replace("T", " ")[:16]

            mensaje = f"🎪 <b>¡RESUMEN DIARIO CRAZY MONITOR!</b> 🎡\n"
            mensaje += f"━━━━━━━━━━━━━━━━━━━━\n"
            mensaje += f"📅 <b>SEMANA {semana} • {dia_semana}</b>\n"
            mensaje += f"🕒 <code>{start_str}</code> ➔ <code>{end_str}</code>\n\n"

            # 2. Análisis de Ventanas (Foco Estratégico)
            mensaje += "🎯 <b>CAZANDO LA VENTAJA</b>\n"
            
            patterns_data = data.get("patterns", [])
            for p in patterns_data:
                mensaje += f"━━━━━━━━━━━━━━━━━━━━\n"
                mensaje += f"🎰 <b>{p['name'].upper()}</b>\n"
                mensaje += f"✨ Apariciones: <b>{p['count']}</b>\n"
                
                if 'windows' in p and p['windows']:
                    for w in p['windows']:
                        # Calcular el rango real de la ventana para el reporte
                        w_start, w_end = get_window_range(w['threshold'])
                        mensaje += f"  📍 <b>Ventana [{w_start}-{w_end}]</b>\n"
                        mensaje += f"    ✅ Aciertos: <b>{w['hits']}</b>\n"
                        mensaje += f"    ❌ Fallos:   <b>{w['misses']}</b>\n"
                else:
                    mensaje += "  💨 <i>Sin oportunidades de ventana hoy...</i>\n"

            # 3. Salud del Sistema (Latidos)
            l = data.get("latidos", {})
            total_l = sum(l.values()) if l else 0
            
            mensaje += f"\n━━━━━━━━━━━━━━━━━━━━\n"
            mensaje += "🛡️ <b>ESTABILIDAD DEL SISTEMA</b>\n"
            if total_l > 0:
                mensaje += f"💎 5s (Ideal):  <b>{l.get('5s', 0)}</b> ({(l.get('5s', 0)/total_l)*100:.1f}%)\n"
                mensaje += f"⚡ 0-4s:        <b>{l.get('0_4s', 0)}</b> ({(l.get('0_4s', 0)/total_l)*100:.1f}%)\n"
                mensaje += f"🐢 6-11s:       <b>{l.get('6_11s', 0)}</b> ({(l.get('6_11s', 0)/total_l)*100:.1f}%)\n"
                mensaje += f"⚠️ Gaps >11s:   <b>{l.get('gt11s', 0)}</b> ({(l.get('gt11s', 0)/total_l)*100:.1f}%)\n"
                mensaje += f"🚫 Negativos:   <b>{l.get('neg', 0)}</b> ({(l.get('neg', 0)/total_l)*100:.1f}%)\n"
            else:
                mensaje += "❓ Sin datos de latidos registrados.\n"

            # 4. Cierre
            mensaje += f"━━━━━━━━━━━━━━━━━━━━\n"
            mensaje += f"🔢 <b>Total spins del periodo:</b> <code>{data.get('total_spins', 0)}</code>\n"
            mensaje += f"💰 <i>¡Mañana más y mejor ventaja!</i> 💰"

            return self.send_message(mensaje.strip())
        except Exception as e:
            logger.error(f"❌ Error enviando resumen diario: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"❌ Error enviando resumen diario: {e}", exc_info=True)
            return False
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
