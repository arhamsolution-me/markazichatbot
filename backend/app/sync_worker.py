import asyncio
import json
import logging
from datetime import datetime, timezone
import psycopg
from psycopg.rows import dict_row
from app.config import settings
from app.db import db_manager
from app.vector_store import vector_store

logger = logging.getLogger("markazi.sync")

class DatabaseSyncWorker:
    def __init__(self):
        self.last_sync_time = datetime.min
        self.is_running = False

    def _sync_service_enums(self, src, hub):
        enums = src.execute("""
            SELECT t.typname, array_agg(e.enumlabel ORDER BY e.enumsortorder) as labels
            FROM pg_type t
            JOIN pg_enum e ON t.oid = e.enumtypid
            JOIN pg_namespace n ON n.oid = t.typnamespace
            WHERE n.nspname = 'public'
            GROUP BY t.typname;
        """).fetchall()
        for e in enums:
            t_name = e["typname"]
            labels = e["labels"]
            exists = hub.execute("SELECT 1 FROM pg_type WHERE typname = %s", (t_name,)).fetchone()
            if not exists:
                labels_str = ", ".join(f"'{lbl}'" for lbl in labels)
                hub.execute(f'CREATE TYPE public."{t_name}" AS ENUM ({labels_str});')  # NOSONAR - values from pg_catalog, not user input

    def _sync_service_table(self, src, hub, target_schema: str, table: str):
        cols = src.execute("""
            SELECT column_name, data_type, udt_name, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position;
        """, (table,)).fetchall()

        if not cols:
            return

        col_defs = []
        for col in cols:
            cname = f'"{col["column_name"]}"'
            dtype = col["data_type"]
            udt = col["udt_name"]
            if dtype == "USER-DEFINED":
                dtype = f'public."{udt}"'
            elif dtype == "ARRAY":
                dtype = f'public."{udt}"[]' if udt.startswith("_") else f'{udt}[]'
            col_defs.append(f"{cname} {dtype}")

        create_sql = f'CREATE TABLE IF NOT EXISTS {target_schema}."{table}" ({", ".join(col_defs)});'  # NOSONAR - values from information_schema, not user input
        hub.execute(create_sql)

        rows = src.execute(f'SELECT * FROM public."{table}"').fetchall()  # NOSONAR - table name from information_schema
        hub.execute(f'TRUNCATE TABLE {target_schema}."{table}" CASCADE;')  # NOSONAR - table name from information_schema
        if rows:
            col_names = [f'"{c["column_name"]}"' for c in cols]
            placeholders = ", ".join(["%s"] * len(cols))
            insert_sql = f'INSERT INTO {target_schema}."{table}" ({", ".join(col_names)}) VALUES ({placeholders})'  # NOSONAR - column names from information_schema
            with hub.cursor() as cur:
                for r in rows:
                    vals = []
                    for c in cols:
                        v = r[c["column_name"]]
                        if isinstance(v, (dict, list)) and c["data_type"] in ("json", "jsonb"):
                            vals.append(json.dumps(v))
                        else:
                            vals.append(v)
                    cur.execute(insert_sql, vals)

    def _sync_service(self, src_dsn: str, is_dsn: str, target_schema: str, tables: list[str]):
        if not src_dsn or src_dsn == is_dsn:
            return
        try:
            with psycopg.connect(src_dsn, row_factory=dict_row) as src, psycopg.connect(is_dsn, autocommit=True) as hub:
                self._sync_service_enums(src, hub)
                hub.execute(f"CREATE SCHEMA IF NOT EXISTS {target_schema};")
                for table in tables:
                    self._sync_service_table(src, hub, target_schema, table)
            logger.info(f"Auto-synced microservice {target_schema.upper()} data to hub.")
        except Exception as err:
            logger.warning(f"Error syncing {target_schema} service: {err}")

    def _sync_remote_services_sync(self):
        """Syncs US and LS microservices tables into the hub database."""
        if not getattr(settings, "US_DB_URL", None) and not getattr(settings, "LS_DB_URL", None):
            return

        is_dsn = settings.DB_URL
        services = [
            (settings.US_DB_URL, "us", ["users", "roles", "permissions", "role_permissions", "widgets", "theme_settings"]),
            (settings.LS_DB_URL, "ls", ["license", "invoice", "service_providers"])
        ]
        for src_dsn, target_schema, tables in services:
            self._sync_service(src_dsn, is_dsn, target_schema, tables)

    async def _sync_channels_couriers_locations(self):
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

    async def _sync_products_catalog(self):
        existing_entities = vector_store.get_entity_count()
        if existing_entities > 1000:
            logger.info(f"Entity catalog already populated ({existing_entities} entities). Skipping redundant product re-embedding.")
            return

        batch_size = 500
        total_synced_products = 0
        offset = 0
        while offset < 3000:
            res = await db_manager.execute_query(
                'SELECT id, title FROM product WHERE title IS NOT NULL ORDER BY id DESC LIMIT %s OFFSET %s;',
                [batch_size, offset]
            )
            if not res["success"] or not res["rows"]:
                break

            batch = [{"type": "product", "id": r["id"], "name": r["title"]} for r in res["rows"] if r.get("title")]
            vector_store.upsert_entities_batch(batch)
            total_synced_products += len(batch)
            offset += batch_size

        logger.info(f"Synced {total_synced_products} products into entity index.")

    async def _sync_users_and_roles(self):
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

    async def initial_sync(self):
        logger.info("Starting initial entity synchronization to Vector DB...")
        try:
            await asyncio.to_thread(self._sync_remote_services_sync)
            await self._sync_channels_couriers_locations()
            await self._sync_products_catalog()
            await self._sync_users_and_roles()

            self.last_sync_time = datetime.now()
            logger.info("Initial sync completed successfully.")
        except asyncio.CancelledError:
            logger.info("Initial sync cancelled.")
            raise
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
                self.is_running = False
                raise
            except Exception as e:
                logger.error(f"Error in sync worker loop: {e}")

    def stop(self):
        self.is_running = False

sync_worker = DatabaseSyncWorker()
