"""
core/api_client.py - Cliente HTTP para API de CasinoScores.
"""

import time
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

class APIClient:
    """Cliente HTTP robusto para API de CasinoScores"""

    API_URL = (
        "https://api.casinoscores.com/svc-evolution-game-events/api/crazytime"
        "?page=0&size=10&sort=data.settledAt,desc&duration=6"
        "&wheelResults=Pachinko,CashHunt,CrazyBonus,CoinFlip,1,2,5,10"
        "&isTopSlotMatched=true,false&tableId=CrazyTime0000001"
    )

    def __init__(self, max_retries: int = 3, timeout: int = 15):
        self.max_retries = max_retries
        self.timeout = timeout

    def fetch(self) -> list[dict]:
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"API request intento {attempt}/{self.max_retries}")
                response = requests.get(
                    self.API_URL,
                    headers=self._get_headers(),
                    timeout=self.timeout
                )
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ API: {len(data)} registros obtenidos")
                    return data
                elif response.status_code == 429:
                    wait_time = (2 ** attempt) * 2
                    logger.warning(f"⚠️ API rate limit (429), esperando {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"❌ API HTTP {response.status_code}")
                    if attempt < self.max_retries:
                        time.sleep(2 ** attempt)
                        continue
            except requests.exceptions.Timeout:
                logger.warning(f"⚠️ Timeout en intento {attempt}/{self.max_retries}")
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)
                    continue
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"⚠️ Error de conexión: {e}")
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)
                    continue
            except Exception as e:
                logger.error(f"❌ Error inesperado en API: {e}", exc_info=True)
                break
        logger.error("❌ API: Todos los reintentos fallaron")
        return []

    def _get_headers(self) -> dict:
        return {
            "User-Agent": "Mozilla/5.0 (Linux; Android 15; Mobile; rv:121.0) Gecko/121.0 Firefox/121.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://casinoscores.com/",
            "Origin": "https://casinoscores.com"
        }
