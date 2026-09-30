import asyncio
import logging
from datetime import datetime, timezone
from app.db import db_manager
from app.vector_store import vector_store

logger = logging.getLogger("markazi.sync")

class DatabaseSyncWorker:
    def __init__(self):
        self.last_sync_time = datetime.min
        self.is_running = False

    async def initial_sync(self):
        logger.info("Starting initial entity synchronization to Vector DB...")
        try:
            res = await db_manager.execute_query('SELECT id, "channelName" FROM channel;')
            if res["success"]:
                for r in res["rows"]:
                    vector_store.upsert_entity("channel", r["id"], r["channelName"])
                logger.info(f"Synced {len(res['rows'])} channels.")

            res = await db_manager.execute_query('SELECT id, "courierName" FROM courier;')
            if res["success"]:
                for r in res["rows"]:
                    vector_store.upsert_entity("courier", r["id"], r["courierName"])
                logger.info(f"Synced {len(res['rows'])} couriers.")

            res = await db_manager.execute_query('SELECT id, name FROM location WHERE "isActive" = true;')
            if res["success"]:
                for r in res["rows"]:
                    vector_store.upsert_entity("location", r["id"], r["name"])
                logger.info(f"Synced {len(res['rows'])} active locations.")

            existing_entities = vector_store.get_entity_count()
            if existing_entities > 1000:
                logger.info(f"Entity catalog already populated ({existing_entities} entities). Skipping redundant product re-embedding.")
            else:
                BATCH_SIZE = 500
                total_synced_products = 0
                offset = 0
                while True:
                    res = await db_manager.execute_query(
                        f'SELECT id, title FROM product WHERE title IS NOT NULL ORDER BY id DESC LIMIT {BATCH_SIZE} OFFSET {offset};'
                    )
                    if not res["success"] or not res["rows"]:
                        break

                    batch = [{"type": "product", "id": r["id"], "name": r["title"]} for r in res["rows"] if r.get("title")]
                    vector_store.upsert_entities_batch(batch)
                    total_synced_products += len(batch)
                    offset += BATCH_SIZE
                    if offset >= 3000:
                        break

                logger.info(f"Synced {total_synced_products} products into entity index.")

            res_users = await db_manager.execute_query('SELECT id, name, "staffId" FROM us.users WHERE "isActive" = true;')
            if res_users["success"]:
                for r in res_users["rows"]:
                    if r.get("name"):
                        vector_store.upsert_entity("user", r["id"], r["name"])
                    if r.get("staffId"):
                        vector_store.upsert_entity("staff_id", r["id"], r["staffId"])
                logger.info(f"Synced {len(res_users['rows'])} active users.")

            res_roles = await db_manager.execute_query('SELECT id, title FROM us.roles WHERE "isActive" = true;')
            if res_roles["success"]:
                for r in res_roles["rows"]:
                    if r.get("title"):
                        vector_store.upsert_entity("role", r["id"], r["title"])
                logger.info(f"Synced {len(res_roles['rows'])} user roles.")

            self.last_sync_time = datetime.now()
            logger.info("Initial sync completed successfully.")
        except Exception as e:
            logger.error(f"Error during initial sync: {e}")

    async def run_periodic_sync(self, interval_seconds: int = 30):
        self.is_running = True
        logger.info(f"Periodic sync worker started (interval: {interval_seconds}s).")
        while self.is_running:
            try:
                await asyncio.sleep(interval_seconds)
                res = await db_manager.execute_query(
                    'SELECT id, title, updated_at FROM product WHERE updated_at > %s ORDER BY updated_at ASC LIMIT 200;',
                    [self.last_sync_time]
                )
                if res["success"] and res["rows"]:
                    batch = [{"type": "product", "id": r["id"], "name": r["title"]} for r in res["rows"] if r.get("title")]
                    vector_store.upsert_entities_batch(batch)
                    for r in res["rows"]:
                        if r["updated_at"] and r["updated_at"] > self.last_sync_time:
                            self.last_sync_time = r["updated_at"]
                    logger.info(f"Auto-synced {len(res['rows'])} updated products to Vector DB.")

            except asyncio.CancelledError:
                logger.info("Sync worker cancelled.")
                break
            except Exception as e:
                logger.error(f"Error in sync worker loop: {e}")

    def stop(self):
        self.is_running = False

sync_worker = DatabaseSyncWorker()
