"""
core/collector.py - Recolector de datos desde API.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from core.api_client import APIClient
from core.database import Database

logger = logging.getLogger(__name__)

class DataCollector:
    """Recolector de datos desde CasinoScores API"""

    def __init__(self, db_path: str = "data/db.sqlite3"):
        self.api = APIClient()
        self.db = Database(db_path)

    def fetch_and_store(self) -> int:
        raw_data = self.api.fetch()
        if not raw_data:
            logger.warning("⚠️ No se obtuvieron datos de la API")
            return 0
        transformed = [self._transform(entry) for entry in raw_data]
        transformed = [t for t in transformed if t is not None]
        if not transformed:
            logger.warning("⚠️ No se pudieron transformar los datos")
            return 0
        inserted = self.db.insertar_datos(transformed)
        if inserted > 0:
            logger.info(f"✅ {inserted} registros nuevos insertados")
        else:
            logger.info("ℹ️ Sin cambios (datos ya existentes)")
        return inserted

    def _transform(self, entry: dict) -> Optional[dict]:
        try:
            data = entry.get("data", {})
            outcome = data.get("result", {}).get("outcome", {})
            timestamp_str = data.get("settledAt", "")
            started_at_str = data.get("startedAt", "")
            if timestamp_str.endswith("Z"):
                timestamp_str = timestamp_str.replace("Z", "+00:00")
            try:
                utc_time = datetime.fromisoformat(timestamp_str)
                peru_time = utc_time - timedelta(hours=5)
                settled_at = peru_time.strftime("%Y-%m-%dT%H:%M:%S")
            except:
                settled_at = timestamp_str
            started_at = None
            if started_at_str:
                if started_at_str.endswith("Z"):
                    started_at_str = started_at_str.replace("Z", "+00:00")
                try:
                    utc_start = datetime.fromisoformat(started_at_str)
                    peru_start = utc_start - timedelta(hours=5)
                    started_at = peru_start.strftime("%Y-%m-%dT%H:%M:%S")
                except:
                    pass
            wheel_result = outcome.get("wheelResult", {}).get("wheelSector", "")
            if wheel_result == "CrazyBonus":
                wheel_result = "CrazyTime"
            top_slot = outcome.get("topSlot", {})
            bonus_multiplier = None
            ct_flapper_blue = None
            ct_flapper_green = None
            ct_flapper_yellow = None
            tipo_resultado = outcome.get("wheelResult", {}).get("type", "")
            if tipo_resultado == "BonusRound":
                bonus_info = outcome.get("wheelResult", {}).get("bonus", {})
                if wheel_result in ["Pachinko", "CoinFlip"]:
                    bonus_multiplier = bonus_info.get("bonusMultiplier", {}).get("value")
                elif wheel_result == "CrazyTime":
                    flapper = bonus_info.get("flapperResult", {})
                    ct_flapper_blue = flapper.get("top", {}).get("bonusMultiplier")
                    ct_flapper_green = flapper.get("left", {}).get("bonusMultiplier")
                    ct_flapper_yellow = flapper.get("right", {}).get("bonusMultiplier")
            return {
                "resultado": wheel_result,
                "settled_at": settled_at,
                "started_at": started_at,
                "top_slot_result": top_slot.get("wheelSector", ""),
                "top_slot_multiplier": top_slot.get("multiplier"),
                "is_top_slot_matched": outcome.get("isTopSlotMatchedToWheelResult", False),
                "bonus_multiplier": bonus_multiplier,
                "ct_flapper_blue": ct_flapper_blue,
                "ct_flapper_green": ct_flapper_green,
                "ct_flapper_yellow": ct_flapper_yellow
            }
        except Exception as e:
            logger.error(f"Error transformando entry: {e}")
            return None
