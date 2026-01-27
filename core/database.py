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
        self._ensure_database_exists()
        self._verify_integrity()

    def _ensure_database_exists(self):
        if os.path.exists(self.db_path):
            return
        logger.warning(f"⚠️ Base de datos no existe, creando: {self.db_path}")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        self._create_schema(conn)
        conn.close()
        logger.info("✅ Base de datos creada")

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
            conn.close()
            logger.info("✅ Integridad de BD verificada")
        except Exception as e:
            logger.critical(f"💥 Error verificando integridad: {e}")
            raise

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
                    current_end = dato.get("timestamp") # Fin del tiro según API
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

    def get_spins_after_pseudo_id(self, after_pseudo_id: int, limit: Optional[int] = None) -> list[dict]:
        try:
            conn = self.get_connection(read_only=True)
            cur = conn.cursor()
            
            # Usar pseudo_id como id para mantener compatibilidad en el dict
            query = """
                SELECT pseudo_id as id, resultado, timestamp, settled_at, latido, 
                       top_slot_result, top_slot_multiplier, is_top_slot_matched,
                       bonus_multiplier, ct_flapper_blue, ct_flapper_green, ct_flapper_yellow
                FROM tiros_ordenados 
                WHERE pseudo_id > ? 
                ORDER BY pseudo_id ASC
            """
            
            if limit:
                cur.execute(query + " LIMIT ?", (after_pseudo_id, limit))
            else:
                cur.execute(query, (after_pseudo_id,))

            rows = cur.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error obteniendo tiros después de pseudo_id {after_pseudo_id}: {e}")
            return []

    def get_last_pattern_pseudo_id(self, value: str) -> Optional[int]:
        """Obtiene el último pseudo_id de un patrón específico"""
        try:
            conn = self.get_connection(read_only=True)
            cur = conn.cursor()
            cur.execute("SELECT MAX(pseudo_id) FROM tiros_ordenados WHERE resultado = ?", (value,))
            result = cur.fetchone()[0]
            conn.close()
            return result
        except Exception as e:
            logger.error(f"Error obteniendo último pseudo_id de {value}: {e}")
            return None

    def get_max_pseudo_id(self) -> Optional[int]:
        """Obtiene el pseudo_id más alto actual"""
        try:
            conn = self.get_connection(read_only=True)
            cur = conn.cursor()
            cur.execute("SELECT MAX(pseudo_id) FROM tiros_ordenados")
            result = cur.fetchone()[0]
            conn.close()
            return result
        except Exception as e:
            logger.error(f"Error obteniendo max pseudo_id: {e}")
            return None

    def get_spin_by_pseudo_id(self, pseudo_id: int) -> Optional[dict]:
        """Obtiene un tiro completo por su pseudo_id"""
        try:
            conn = self.get_connection(read_only=True)
            cur = conn.cursor()
            cur.execute("SELECT pseudo_id as id, * FROM tiros_ordenados WHERE pseudo_id = ?", (pseudo_id,))
            row = cur.fetchone()
            conn.close()
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"Error obteniendo tiro por pseudo_id {pseudo_id}: {e}")
            return None

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

    def obtener_estadisticas_dia(self, fecha: Optional[str] = None) -> dict:
        conn = None
        try:
            if not fecha:
                fecha = (datetime.now() - timedelta(hours=5)).strftime("%Y-%m-%d")
            conn = self.get_connection(read_only=True)
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM tiros_ordenados WHERE DATE(timestamp) = ?", (fecha,))
            total_spins = cur.fetchone()[0]
            cur.execute("""
                SELECT resultado, COUNT(*)
                FROM tiros_ordenados
                WHERE DATE(timestamp) = ?
                GROUP BY resultado
            """, (fecha,))
            conteos = dict(cur.fetchall())
            conn.close()
            return {
                "total_spins": total_spins,
                "1": conteos.get("1", 0), "2": conteos.get("2", 0),
                "5": conteos.get("5", 0), "10": conteos.get("10", 0),
                "CoinFlip": conteos.get("CoinFlip", 0),
                "CashHunt": conteos.get("CashHunt", 0),
                "Pachinko": conteos.get("Pachinko", 0),
                "CrazyTime": conteos.get("CrazyTime", 0)
            }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {"total_spins": 0}
        finally:
            if conn:
                conn.close()
