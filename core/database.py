"""
core/database.py - Capa de acceso a datos SQLite.
"""

import os
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

class Database:
    """Capa de acceso a datos con SQLite"""

    def __init__(self, db_path: str = "data/db.sqlite3"):
        self.db_path = db_path
        self._ensure_schema()
        self._verify_integrity()

    def _ensure_schema(self):
        """Asegura que la base de datos y todas sus tablas existan."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        # Siempre abrimos conexión para garantizar que el esquema esté al día
        try:
            conn = sqlite3.connect(self.db_path)
            self._create_schema(conn)
            conn.close()
        except Exception as e:
            logger.critical(f"💥 Error inicializando esquema: {e}")
            raise

    def _create_schema(self, conn: sqlite3.Connection):
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tiros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resultado TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                started_at TEXT,
                settled_at TEXT,
                latido INTEGER DEFAULT 0,
                top_slot_result TEXT,
                top_slot_multiplier INTEGER,
                is_top_slot_matched BOOLEAN,
                bonus_multiplier INTEGER,
                ct_flapper_blue INTEGER,
                ct_flapper_green INTEGER,
                ct_flapper_yellow INTEGER
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_resultado ON tiros(resultado)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON tiros(timestamp)")
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_timestamp_unique ON tiros(timestamp)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_resultado_timestamp ON tiros(resultado, timestamp)")
        
        # FASE 2: Vista de Pseudo IDs Cronológicos
        cur.execute("""
            CREATE VIEW IF NOT EXISTS tiros_ordenados AS
            SELECT 
                ROW_NUMBER() OVER (ORDER BY timestamp ASC) AS pseudo_id,
                *
            FROM tiros
        """)
        
        # FASE 3: Tabla de Estado del Sistema (Persistencia Robusta)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS system_state (
                module TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (module, key)
            )
        """)
        
        conn.commit()

    def _verify_integrity(self):
        """Verifica integridad de la base de datos"""
        try:
            conn = self.get_connection(read_only=True)
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tiros'")
            if not cur.fetchone():
                logger.error("❌ Tabla 'tiros' no existe")
                conn.close()
                raise RuntimeError("Tabla 'tiros' faltante")
            
            # Verificar system_state
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='system_state'")
            if not cur.fetchone():
                logger.warning("⚠️ Tabla 'system_state' no existe, se creará en próxima conexión de escritura")
            
            conn.close()
            logger.info("✅ Integridad de BD verificada")
        except Exception as e:
            logger.critical(f"💥 Error verificando integridad: {e}")
            raise

    def get_state(self, module: str, key: str, default=None):
        """Obtiene un valor de estado del sistema."""
        try:
            conn = self.get_connection(read_only=True)
            cur = conn.cursor()
            cur.execute("SELECT value FROM system_state WHERE module = ? AND key = ?", (module, key))
            row = cur.fetchone()
            conn.close()
            if row:
                import json
                return json.loads(row[0])
            return default
        except Exception as e:
            logger.error(f"Error leyendo estado ({module}.{key}): {e}")
            return default

    def set_state(self, module: str, key: str, value):
        """Guarda un valor de estado del sistema (UPSERT)."""
        try:
            import json
            json_val = json.dumps(value)
            conn = self.get_connection(read_only=False)
            cur = conn.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO system_state (module, key, value, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (module, key, json_val))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error guardando estado ({module}.{key}): {e}")

    def get_connection(self, read_only: bool = False) -> sqlite3.Connection:
        """
        Obtiene conexión a la base de datos.

        Args:
            read_only: Si True, abre en modo solo lectura

        Returns:
            Conexión configurada con WAL mode
        """
        try:
            if read_only:
                conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True, timeout=20)
            else:
                conn = sqlite3.connect(self.db_path, timeout=20)
            if not read_only:
                conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            logger.error(f"❌ Error conectando a BD: {e}")
            raise

    def insertar_datos(self, datos: list[dict]) -> int:
        if not datos:
            return 0
        conn = None
        insertados = 0
        try:
            conn = self.get_connection(read_only=False)
            cur = conn.cursor()

            # Ordenar por inicio real para asegurar cronología
            datos_ordenados = sorted(datos, key=lambda x: x.get("started_at", ""))

            for dato in datos_ordenados:
                try:
                    current_start = dato.get("started_at")
                    current_end = dato.get("settled_at") # Fin del tiro
                    current_resultado = dato["resultado"]

                    if not current_start or not current_end:
                        continue

                    # 1. Filtro de duplicados (±10s sobre inicio real) - Buscando de nuevo a viejo
                    cur.execute("""
                        SELECT id, timestamp FROM tiros 
                        WHERE resultado = ? 
                        AND datetime(timestamp) BETWEEN datetime(?, '-10 seconds') AND datetime(?, '+10 seconds')
                        ORDER BY id DESC LIMIT 1
                    """, (current_resultado, current_start, current_start))
                    
                    collision = cur.fetchone()
                    if collision:
                        # Solo avisar si hay una anomalía (tiempos diferentes pero en rango 10s)
                        if collision['timestamp'] != current_start:
                            logger.warning(f"⚠️ ANOMALÍA [Filtro 10s]: {current_resultado} ({current_start}) choca con ID #{collision['id']} ({collision['timestamp']})")
                        continue

                    # 2. Calcular Latido Real (Inicio Actual - Fin del Vecino Cronológico Anterior)
                    cur.execute("""
                        SELECT id, settled_at FROM tiros 
                        WHERE timestamp < ? 
                        ORDER BY timestamp DESC LIMIT 1
                    """, (current_start,))
                    last_row = cur.fetchone()
                    
                    latido = 0
                    if last_row and last_row['settled_at']:
                        try:
                            t_prev_end = datetime.fromisoformat(last_row['settled_at'])
                            t_curr_start = datetime.fromisoformat(current_start)
                            latido = int((t_curr_start - t_prev_end).total_seconds())
                        except Exception as e:
                            logger.error(f"❌ Error calculando latido para {current_resultado} ({current_start}): {e}")
                            latido = 0

                    # 3. Insertar con nuevo modelo
                    cur.execute("""
                        INSERT INTO tiros (
                            resultado, timestamp, settled_at, latido,
                            top_slot_result, top_slot_multiplier, is_top_slot_matched,
                            bonus_multiplier, ct_flapper_blue, ct_flapper_green, ct_flapper_yellow
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        current_resultado, current_start, current_end, latido,
                        dato.get("top_slot_result"), dato.get("top_slot_multiplier"),
                        dato.get("is_top_slot_matched", False), dato.get("bonus_multiplier"),
                        dato.get("ct_flapper_blue"), dato.get("ct_flapper_green"), dato.get("ct_flapper_yellow")
                    ))
                    insertados += 1

                except sqlite3.IntegrityError:
                    continue
                except Exception as e:
                    logger.error(f"Error insertando registro: {e}")
                    continue

            conn.commit()
            return insertados
        except Exception as e:
            logger.error(f"❌ Error en inserción batch: {e}")
            if conn:
                conn.rollback()
            return 0
        finally:
            if conn:
                conn.close()

    def get_max_id(self) -> Optional[int]:
        try:
            conn = self.get_connection(read_only=True)
            cur = conn.cursor()
            cur.execute("SELECT MAX(id) FROM tiros")
            result = cur.fetchone()[0]
            conn.close()
            return result
        except Exception as e:
            logger.error(f"Error obteniendo max ID: {e}")
            return None

    def get_last_occurrence_id(self, value: str) -> Optional[int]:
        try:
            conn = self.get_connection(read_only=True)
            cur = conn.cursor()
            cur.execute("SELECT MAX(id) FROM tiros WHERE resultado = ?", (value,))
            result = cur.fetchone()[0]
            conn.close()
            return result
        except Exception as e:
            logger.error(f"Error obteniendo última aparición de {value}: {e}")
            return None

    def get_spin_by_id(self, spin_id: int) -> Optional[dict]:
        try:
            conn = self.get_connection(read_only=True)
            cur = conn.cursor()
            cur.execute("SELECT * FROM tiros WHERE id = ?", (spin_id,))
            row = cur.fetchone()
            conn.close()
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"Error obteniendo tiro {spin_id}: {e}")
            return None

    def get_spins_after_id(self, after_id: int, limit: Optional[int] = None) -> list[dict]:
        try:
            conn = self.get_connection(read_only=True)
            cur = conn.cursor()

            if limit:
                cur.execute("SELECT * FROM tiros WHERE id > ? ORDER BY id ASC LIMIT ?", (after_id, limit))
            else:
                cur.execute("SELECT * FROM tiros WHERE id > ? ORDER BY id ASC", (after_id,))

            rows = cur.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error obteniendo tiros después de {after_id}: {e}")
            return []

    def get_spins_after_pseudo_id(self, after_id: int, limit: Optional[int] = None) -> list[dict]:
        """Alias mantenido por compatibilidad, pero ahora usa IDs reales"""
        return self.get_spins_after_id(after_id, limit)

    def get_last_pattern_pseudo_id(self, value: str) -> Optional[int]:
        """Obtiene el último ID real de un patrón específico"""
        try:
            conn = self.get_connection(read_only=True)
            cur = conn.cursor()
            cur.execute("SELECT MAX(id) FROM tiros WHERE resultado = ?", (value,))
            result = cur.fetchone()[0]
            conn.close()
            return result
        except Exception as e:
            logger.error(f"Error obteniendo último ID de {value}: {e}")
            return None

    def get_max_pseudo_id(self) -> Optional[int]:
        """Obtiene el ID más alto actual de la tabla tiros"""
        return self.get_max_id()

    def get_spin_by_pseudo_id(self, spin_id: int) -> Optional[dict]:
        """Obtiene un tiro completo por su ID real"""
        return self.get_spin_by_id(spin_id)

    def get_last_spin(self) -> Optional[dict]:
        try:
            conn = self.get_connection(read_only=True)
            cur = conn.cursor()
            cur.execute("SELECT * FROM tiros ORDER BY id DESC LIMIT 1")
            row = cur.fetchone()
            conn.close()
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"Error obteniendo último tiro: {e}")
            return None

    def obtener_estadisticas_rango(self, start_iso: str, end_iso: str) -> dict:
        """
        Obtiene estadísticas de tiros en un rango de tiempo específico.
        Neutral: No calcula fechas, solo consulta lo solicitado.
        """
        conn = None
        try:
            conn = self.get_connection(read_only=True)
            cur = conn.cursor()
            
            # 1. Total de spins
            cur.execute("""
                SELECT COUNT(*) FROM tiros 
                WHERE timestamp >= ? AND timestamp < ?
            """, (start_iso, end_iso))
            total_spins = cur.fetchone()[0]
            
            # 2. Conteos por resultado
            cur.execute("""
                SELECT resultado, COUNT(*)
                FROM tiros
                WHERE timestamp >= ? AND timestamp < ?
                GROUP BY resultado
            """, (start_iso, end_iso))
            conteos = dict(cur.fetchall())

            # 3. Estadísticas de Latidos
            cur.execute("""
                SELECT 
                    SUM(CASE WHEN latido = 5 THEN 1 ELSE 0 END) as l_5,
                    SUM(CASE WHEN latido >= 0 AND latido <= 4 THEN 1 ELSE 0 END) as l_0_4,
                    SUM(CASE WHEN latido >= 6 AND latido <= 11 THEN 1 ELSE 0 END) as l_6_11,
                    SUM(CASE WHEN latido > 11 THEN 1 ELSE 0 END) as l_gt11,
                    SUM(CASE WHEN latido < 0 THEN 1 ELSE 0 END) as l_neg
                FROM tiros
                WHERE timestamp >= ? AND timestamp < ?
            """, (start_iso, end_iso))
            
            l_stats = cur.fetchone()
            latidos = {
                "5s": l_stats['l_5'] or 0,
                "0_4s": l_stats['l_0_4'] or 0,
                "6_11s": l_stats['l_6_11'] or 0,
                "gt11s": l_stats['l_gt11'] or 0,
                "neg": l_stats['l_neg'] or 0
            }

            conn.close()
            
            return {
                "total_spins": total_spins,
                "range_start": start_iso,
                "range_end": end_iso,
                "counts": {
                    "1": conteos.get("1", 0), "2": conteos.get("2", 0),
                    "5": conteos.get("5", 0), "10": conteos.get("10", 0),
                    "CoinFlip": conteos.get("CoinFlip", 0),
                    "CashHunt": conteos.get("CashHunt", 0),
                    "Pachinko": conteos.get("Pachinko", 0),
                    "CrazyTime": conteos.get("CrazyTime", 0)
                },
                "latidos": latidos
            }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas en rango: {e}")
            return {"total_spins": 0}
        finally:
            if conn:
                conn.close()

    def obtener_estadisticas_dia(self, fecha: Optional[str] = None) -> dict:
        """Wrapper mantenido por compatibilidad, calcula el día natural."""
        now = datetime.now()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        return self.obtener_estadisticas_rango(start.isoformat(), end.isoformat())
