import time
import asyncio
import logging
from typing import Any, Optional
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row
from app.config import settings

logger = logging.getLogger("markazi.db")

class DatabaseManager:
    def __init__(self):
        self.pool: Optional[ConnectionPool] = None

    def initialize(self):
        if not self.pool:
            logger.info("Initializing PostgreSQL Connection Pool...")
            self.pool = ConnectionPool(
                conninfo=settings.DB_URL,
                min_size=settings.DB_MIN_CONNECTIONS,
                max_size=settings.DB_MAX_CONNECTIONS,
                max_idle=120.0,
                check=ConnectionPool.check_connection,
                kwargs={"row_factory": dict_row}
            )
            logger.info("PostgreSQL Pool is open and ready.")

    def close(self):
        if self.pool:
            logger.info("Closing PostgreSQL Connection Pool...")
            self.pool.close()
            self.pool = None

    def _sync_execute(self, query: str, params: Optional[dict | list] = None) -> dict[str, Any]:
        if not self.pool:
            self.initialize()

        start_time = time.perf_counter()
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SET TRANSACTION READ ONLY;")
                cur.execute("SET search_path TO public, us, ls;")
                cur.execute(f"SET statement_timeout = '{settings.DB_QUERY_TIMEOUT_MS}';")
                cur.execute(query, params)
                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                
                if cur.description:
                    columns = [desc[0] for desc in cur.description]
                    rows = cur.fetchall()
                    return {
                        "success": True,
                        "columns": columns,
                        "rows": rows,
                        "row_count": len(rows),
                        "duration_ms": duration_ms,
                        "error": None
                    }
                else:
                    return {
                        "success": True,
                        "columns": [],
                        "rows": [],
                        "row_count": 0,
                        "duration_ms": duration_ms,
                        "error": None
                    }

    async def execute_query(self, query: str, params: Optional[dict | list] = None) -> dict[str, Any]:
        return await asyncio.to_thread(self._sync_execute, query, params)

db_manager = DatabaseManager()
