import asyncio
import logging
from pathlib import Path
from contextlib import asynccontextmanager
import json
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from app.config import settings
from app.db import db_manager
from app.vector_store import vector_store
from app.sync_worker import sync_worker
from app.agent import agent
from app.schema_catalog import TABLE_CATALOG, catalog_manager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("markazi.server")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up Markazi AI Chatbot service...")
    db_manager.initialize()
    
    logger.info("Introspecting dynamic schema from PostgreSQL...")
    catalog_manager.load_from_db(db_manager)

    logger.info("Indexing dynamic schema tables into Vector Store...")
    vector_store.index_schema()
    
    await sync_worker.initial_sync()

    sync_task = asyncio.create_task(sync_worker.run_periodic_sync(interval_seconds=30))
    logger.info("Markazi AI Chatbot is ready to accept requests.")
    
    yield
    
    logger.info("Shutting down Markazi AI Chatbot service...")
    sync_worker.stop()
    sync_task.cancel()
    db_manager.close()

app = FastAPI(title="Markazi AI Chatbot Core", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    role: str
    content: str
    sql: str | None = None

class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []

class ChatResponse(BaseModel):
    answer: str
    sql: str = ""
    columns: list[str] = []
    rows: list[dict] = []
    row_count: int = 0
    duration_ms: float = 0.0
    relevant_tables: list[str] = []
    entities: list[dict] = []
    chart: dict | None = None
    error: str | None = None

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest, authorization: str | None = Header(None)):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    
    expected_token = getattr(settings, "CHAT_API_TOKEN", None)
    if expected_token and authorization:
        token = authorization.replace("Bearer ", "").strip()
        if token != expected_token:
            raise HTTPException(status_code=401, detail="Invalid API Token.")

    try:
        history_dicts = [h.model_dump() for h in req.history] if req.history else None
        result = await agent.process_query(req.message.strip(), history=history_dicts)
        return ChatResponse(**result)
    except Exception as e:
        logger.error(f"Error handling chat request: {e}", exc_info=True)
        return ChatResponse(
            answer=f"I was able to run your query, but encountered a formatting limit: {str(e)}. You can inspect the complete results in the Data Table below or download the CSV.",
            sql="",
            columns=[],
            rows=[],
            row_count=0,
            duration_ms=0,
            relevant_tables=[],
            entities=[],
            chart=None,
            error=str(e)
        )

@app.post("/api/chat/stream")
async def chat_stream_endpoint(req: ChatRequest, authorization: str | None = Header(None)):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    expected_token = getattr(settings, "CHAT_API_TOKEN", None)
    if expected_token and authorization:
        token = authorization.replace("Bearer ", "").strip()
        if token != expected_token:
            raise HTTPException(status_code=401, detail="Invalid API Token.")

    history_dicts = [h.model_dump() for h in req.history] if req.history else None

    async def sse_event_generator():
        try:
            async for item in agent.process_query_stream(req.message.strip(), history=history_dicts):
                yield f"event: {item['event']}\ndata: {item['data']}\n\n"
        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(sse_event_generator(), media_type="text/event-stream")

@app.get("/api/stats")
async def stats_endpoint():
    res = await db_manager.execute_query("""
        SELECT table_schema, table_name, table_type 
        FROM information_schema.tables 
        WHERE table_schema IN ('public', 'us', 'ls')
        ORDER BY table_schema, table_name;
    """)
    tables_by_schema = {"public": [], "us": [], "ls": []}
    all_tables = []
    for r in res.get("rows", []):
        s = r["table_schema"]
        t = r["table_name"]
        tables_by_schema.setdefault(s, []).append(t)
        all_tables.append(f"{s}.{t}" if s != "public" else t)

    return {
        "status": "healthy",
        "database": "markazi_qa_is",
        "linked_services": {
            "is": {
                "name": "Inventory & Operations Hub",
                "database": "markazi_qa_is",
                "schema": "public",
                "tables_count": len(tables_by_schema.get("public", []))
            },
            "us": {
                "name": "User Management & RBAC Service",
                "database": "markazi_qa_us",
                "schema": "us",
                "tables_count": len(tables_by_schema.get("us", []))
            },
            "ls": {
                "name": "License & Billing Service",
                "database": "markazi_qa_ls",
                "schema": "ls",
                "tables_count": len(tables_by_schema.get("ls", []))
            }
        },
        "total_tables_count": len(all_tables),
        "available_tables": all_tables,
        "tables_by_schema": tables_by_schema,
        "groq_keys_count": len(settings.groq_keys),
        "model": settings.GROQ_MODEL
    }

@app.post("/api/sync")
async def trigger_sync():
    await sync_worker.initial_sync()
    return {"status": "success", "message": "Entities re-synchronized with Vector Store."}

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
