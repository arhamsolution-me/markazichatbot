import os
import logging
from typing import Any, Optional
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from fastembed import TextEmbedding
from app.config import settings
from app.schema_catalog import TABLE_CATALOG, catalog_manager

logger = logging.getLogger("markazi.vector")

COLLECTION_SCHEMA = "schema_catalog"
COLLECTION_ENTITIES = "entity_catalog"
VECTOR_SIZE = 384

class VectorStore:
    def __init__(self):
        Path(settings.QDRANT_STORAGE_PATH).mkdir(parents=True, exist_ok=True)
        try:
            self.client = QdrantClient(path=settings.QDRANT_STORAGE_PATH)
            logger.info(f"Qdrant initialized with persistent storage at {settings.QDRANT_STORAGE_PATH}")
        except Exception as e:
            logger.warning(f"Could not open persistent Qdrant ({e}). Falling back to in-memory Qdrant.")
            self.client = QdrantClient(location=":memory:")

        logger.info(f"Loading FastEmbed model {settings.EMBEDDING_MODEL_NAME}...")
        self.embed_model = TextEmbedding(model_name=settings.EMBEDDING_MODEL_NAME)
        self._ensure_collections()

    def _ensure_collections(self):
        existing = [c.name for c in self.client.get_collections().collections]
        if COLLECTION_SCHEMA not in existing:
            self.client.create_collection(
                collection_name=COLLECTION_SCHEMA,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
            )
            logger.info(f"Created collection '{COLLECTION_SCHEMA}'.")

        if COLLECTION_ENTITIES not in existing:
            self.client.create_collection(
                collection_name=COLLECTION_ENTITIES,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
            )
            logger.info(f"Created collection '{COLLECTION_ENTITIES}'.")

    def _get_embedding(self, text: str) -> list[float]:
        vectors = list(self.embed_model.embed([text]))
        return [float(x) for x in vectors[0]]

    def _get_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        vectors = list(self.embed_model.embed(texts))
        return [[float(x) for x in v] for v in vectors]

    def get_entity_count(self) -> int:
        try:
            return self.client.get_collection(COLLECTION_ENTITIES).points_count or 0
        except Exception as e:  # noqa: BLE001
            logger.debug("Could not retrieve entity collection count: %s", e)
            return 0

    def index_schema(self):
        catalog = catalog_manager.get_catalog()
        if not catalog:
            logger.warning("Dynamic catalog is empty, skipping schema indexing.")
            return

        points = []
        point_id = 1
        seen_keys = set()
        for table_key, info in catalog.items():
            unique_ident = f"{info.get('schema', 'public')}.{info.get('table_name', table_key)}"
            if unique_ident in seen_keys:
                continue
            seen_keys.add(unique_ident)

            col_list = ", ".join([c[0] for c in info.get("columns", [])])
            content = (
                f"Table {info.get('quoted_name', table_key)} ({info.get('description', '')}). "
                f"Service: {info.get('service', '')}. "
                f"Concepts: {info.get('concepts', '')}. "
                f"Synonyms: {info.get('synonyms', '')}. "
                f"Columns: {col_list}"
            )
            vector = self._get_embedding(content)
            points.append(
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "table_name": info.get("table_name", table_key),
                        "schema": info.get("schema", "public"),
                        "quoted_name": info.get("quoted_name", table_key),
                        "description": info.get("description", "")
                    }
                )
            )
            point_id += 1

        self.client.upsert(collection_name=COLLECTION_SCHEMA, points=points)
        logger.info(f"Dynamically indexed {len(points)} multi-service tables into '{COLLECTION_SCHEMA}'.")

    def _match_by_catalog_keywords(self, catalog: dict[str, Any], q_lower: str) -> list[str]:
        matched: list[str] = []
        for t_name, info in catalog.items():
            short_name = info.get("table_name", t_name)
            if short_name in matched:
                continue

            if t_name.lower() in q_lower or info.get("quoted_name", "").strip('"').lower() in q_lower:
                matched.append(short_name)
                continue

            synonyms_str = info.get("synonyms", "")
            if synonyms_str:
                syn_list = [s.strip().lower() for s in synonyms_str.split(",") if len(s.strip()) > 2]
                for syn in syn_list:
                    if syn in q_lower or (len(syn) > 4 and syn[:-1] in q_lower):
                        matched.append(short_name)
                        break
        return matched

    def _match_by_vector_search(self, query: str, top_k: int) -> list[str]:
        matched: list[str] = []
        try:
            vector = self._get_embedding(query)
            try:
                results = self.client.query_points(
                    collection_name=COLLECTION_SCHEMA,
                    query=vector,
                    limit=top_k
                ).points
            except Exception as e:  # noqa: BLE001
                logger.debug("query_points not available, falling back to legacy search: %s", e)
                results = self.client.search(
                    collection_name=COLLECTION_SCHEMA,
                    query_vector=vector,
                    limit=top_k
                )

            for hit in results:
                tbl = hit.payload.get("table_name")
                if tbl and tbl not in matched:
                    matched.append(tbl)
        except Exception as e:
            logger.warning(f"Semantic schema search fallback error: {e}")
        return matched

    def _expand_dependencies(self, tables: list[str], dynamic_deps: dict[str, list[str]]) -> list[str]:
        expanded = list(tables)
        for _ in range(2):
            snapshot = tuple(expanded)
            for tbl in snapshot:
                for dep in dynamic_deps.get(tbl, []):
                    if dep not in expanded:
                        expanded.append(dep)
        return expanded

    def search_relevant_tables(self, query: str, top_k: int = 30) -> list[str]:
        catalog = catalog_manager.get_catalog()
        q_lower = query.lower()
        matched_tables = self._match_by_catalog_keywords(catalog, q_lower)

        for tbl in self._match_by_vector_search(query, top_k):
            if tbl not in matched_tables:
                matched_tables.append(tbl)

        dynamic_deps = catalog_manager.get_dependencies()
        expanded = self._expand_dependencies(matched_tables, dynamic_deps)

        if not expanded:
            expanded = ["order", "order_item", "product", "product_variant", "stock", "location", "users", "roles", "license"]

        return list(dict.fromkeys(expanded))

    def upsert_entity(self, entity_type: str, entity_id: int, name: str):
        if not name:
            return
        vector = self._get_embedding(f"{entity_type} {name}")
        point_id = abs(hash(f"{entity_type}_{entity_id}")) % (2**63 - 1)
        self.client.upsert(
            collection_name=COLLECTION_ENTITIES,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "type": entity_type,
                        "id": entity_id,
                        "name": name
                    }
                )
            ]
        )

    def upsert_entities_batch(self, entities: list[dict]):
        valid_entities = [e for e in entities if e.get("name")]
        if not valid_entities:
            return
        
        texts = [f"{e['type']} {e['name']}" for e in valid_entities]
        vectors = self._get_embeddings_batch(texts)
        
        points = []
        for e, v in zip(valid_entities, vectors):
            point_id = abs(hash(f"{e['type']}_{e['id']}")) % (2**63 - 1)
            points.append(
                PointStruct(
                    id=point_id,
                    vector=v,
                    payload={
                        "type": e["type"],
                        "id": e["id"],
                        "name": e["name"]
                    }
                )
            )
        
        self.client.upsert(collection_name=COLLECTION_ENTITIES, points=points)

    def search_entities(self, query: str, top_k: int = 50, score_threshold: float = 0.45) -> list[dict]:
        vector = self._get_embedding(query)
        try:
            results = self.client.query_points(
                collection_name=COLLECTION_ENTITIES,
                query=vector,
                limit=top_k,
                score_threshold=score_threshold
            ).points
        except Exception as e:  # noqa: BLE001
            logger.debug("query_points not available, falling back to legacy search: %s", e)
            try:
                results = self.client.search(
                    collection_name=COLLECTION_ENTITIES,
                    query_vector=vector,
                    limit=top_k,
                    score_threshold=score_threshold
                )
            except Exception as search_err:  # noqa: BLE001
                logger.warning("Entity search failed with both methods: %s", search_err)
                results = []

        matches = []
        seen = set()
        for hit in results:
            payload = hit.payload
            key = (payload.get("type"), payload.get("id"))
            if key in seen:
                continue
            seen.add(key)
            matches.append({
                "type": payload.get("type"),
                "id": payload.get("id"),
                "name": payload.get("name"),
                "score": round(hit.score, 3)
            })
            if len(matches) >= top_k:
                break
        return matches

vector_store = VectorStore()
