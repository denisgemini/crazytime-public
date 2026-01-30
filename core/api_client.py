"""
core/api_client.py - Cliente HTTP para API de CasinoScores con soporte de paginación.
"""

import time
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

class APIClient:
    """Cliente HTTP robusto para API de CasinoScores"""

    BASE_URL = "https://api.casinoscores.com/svc-evolution-game-events/api/crazytime"
    
    def __init__(self, max_retries: int = 5, timeout: int = 15):
        self.max_retries = max_retries
        self.timeout = timeout

    def fetch(self, page: int = 0, size: int = 10) -> list[dict]:
        # Construcción dinámica de URL
        url = (
            f"{self.BASE_URL}"
            f"?page={page}&size={size}"
            "&sort=data.settledAt,desc&duration=6"
            "&wheelResults=Pachinko,CashHunt,CrazyBonus,CoinFlip,1,2,5,10"
            "&isTopSlotMatched=true,false&tableId=CrazyTime0000001"
        )

        for attempt in range(1, self.max_retries + 1):
            try:
                # Logger silencioso para intentos normales, ruidoso para reintentos
                if attempt > 1:
                    logger.debug(f"API request intento {attempt}/{self.max_retries} (Page {page})")
                
                response = requests.get(
                    url,
                    headers=self._get_headers(),
                    timeout=self.timeout
                )
                if response.status_code == 200:
                    data = response.json()
                    # logger.info(f"✅ API (P{page}): {len(data)} registros obtenidos") 
                    # Comentado para no spamear en modo recursivo
                    return data
                elif response.status_code == 429:
                    wait_time = (attempt * 5)
                    logger.warning(f"⚠️ API rate limit (429), esperando {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"❌ API HTTP {response.status_code}")
                    if attempt < self.max_retries:
                        time.sleep(attempt * 2)
                        continue
            except Exception as e:
                logger.warning(f"⚠️ Error API ({e}). Reintentando...")
                if attempt < self.max_retries:
                    time.sleep(attempt * 2)
                    continue
        
        logger.error(f"❌ API: Fallo total en Page {page}")
        return []

    def _get_headers(self) -> dict:
        return {
            "User-Agent": "Mozilla/5.0 (Linux; Android 15; Mobile; rv:121.0) Gecko/121.0 Firefox/121.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://casinoscores.com/",
            "Origin": "https://casinoscores.com"
        }