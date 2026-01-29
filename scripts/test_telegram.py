
import os
import asyncio
from dotenv import load_dotenv
from telegram import Bot

async def test_bot():
    load_dotenv()
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("❌ Error: Credenciales no encontradas en .env")
        return

    bot = Bot(token=token)
    try:
        await bot.send_message(chat_id=chat_id, text="✅ **CRAZYTIME MONITOR**\n\nConexión establecida con éxito. Las alertas están activas.", parse_mode="Markdown")
        print("✅ Mensaje enviado con éxito a Telegram")
    except Exception as e:
        print(f"❌ Error enviando mensaje: {e}")

if __name__ == "__main__":
    asyncio.run(test_bot())
