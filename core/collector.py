"""
core/collector.py - Recolector de datos con Generación de Escalera de Páginas.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List
from core.api_client import APIClient
from core.database import Database

logger = logging.getLogger(__name__)

class DataCollector:
    """Recolector que entrega lotes de datos en orden cronológico para cerrar brechas."""

    GAP_THRESHOLD_SECONDS = 11
    PAGE_SIZE_RECOVERY = 24
    MINUTES_PER_PAGE = 20

    def __init__(self, db_path: str = "data/db.sqlite3"):
        self.api = APIClient()
        self.db = Database(db_path)

    def fetch_batches(self) -> List[List[dict]]:
        """
        Obtiene uno o más lotes de datos. 
        Si hay brecha, devuelve la escalera de páginas [Vieja, ..., Nueva].
        """
        # 1. Intento normal (Page 0)
        raw_data = self.api.fetch(page=0, size=10)
        if not raw_data:
            return []

        clean_batch = self._transform_batch(raw_data)
        if not clean_batch:
            return []

        # 2. Análisis de Continuidad
        last_db_spin = self.db.get_last_spin()
        if not last_db_spin:
            return [clean_batch] # Primer arranque

        # Timestamp de fin del último guardado
        last_settled = last_db_spin.get('settled_at')
        if not last_settled:
            return [clean_batch]

        last_db_end = datetime.fromisoformat(last_settled)
        
        # El más viejo del lote nuevo
        clean_batch_sorted = sorted(clean_batch, key=lambda x: x['started_at'])
        oldest_new_time = datetime.fromisoformat(clean_batch_sorted[0]['started_at'])
        
        gap_seconds = (oldest_new_time - last_db_end).total_seconds()

        if gap_seconds > self.GAP_THRESHOLD_SECONDS:
            logger.warning(f"🚨 BRECHA DETECTADA: {gap_seconds:.1f}s. Generando escalera de recuperación...")
            return self._generate_recovery_stair(last_db_end, gap_seconds)

        return [clean_batch]

    def _generate_recovery_stair(self, last_db_end: datetime, gap_seconds: float) -> List[List[dict]]:
        """Busca el empalme y genera la lista de páginas desde la brecha hasta el presente."""
        gap_minutes = gap_seconds / 60
        calculated_page = int(gap_minutes / self.MINUTES_PER_PAGE)
        
        # Navegación limitada (max 3 saltos desde la calculada)
        found_page = -1
        
        # Probamos calculado, calculado+1, calculado+2, calculado+3
        for offset in range(0, 4):
            test_page = calculated_page + offset
            logger.info(f"📡 Verificando empalme en Page {test_page}...")
            
            raw_page = self.api.fetch(page=test_page, size=self.PAGE_SIZE_RECOVERY)
            if not raw_page: continue
            
            clean_page = self._transform_batch(raw_page)
            if not clean_page: continue
            
            page_sorted = sorted(clean_page, key=lambda x: x['started_at'])
            oldest_in_page = datetime.fromisoformat(page_sorted[0]['started_at'])
            newest_in_page = datetime.fromisoformat(page_sorted[-1]['started_at'])
            
            # ¿Esta página contiene o toca nuestro último dato?
            if oldest_in_page <= last_db_end <= newest_in_page or oldest_in_page < last_db_end:
                found_page = test_page
                logger.info(f"✅ Empalme hallado en Page {found_page}")
                break
        
        if found_page == -1:
            logger.error("❌ No se encontró empalme tras 3 intentos. Recuperando desde Page 0.")
            found_page = 0

        # Generar escalera [Page N, Page N-1, ..., Page 0]
        # (Usamos size 24 para todas para asegurar cobertura total)
        stair = []
        for i in range(found_page, -1, -1):
            logger.info(f"📦 Preparando lote: Page {i}")
            page_data = self.api.fetch(page=i, size=self.PAGE_SIZE_RECOVERY)
            if page_data:
                stair.append(self._transform_batch(page_data))
        
        return stair

    def _transform_batch(self, raw_data: list) -> List[dict]:
        transformed = [self._transform(entry) for entry in raw_data]
        return [t for t in transformed if t is not None]

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