import re
import json
import logging
from typing import Any, Optional
from datetime import datetime
from decimal import Decimal
from app.db import db_manager
from app.security import validate_and_sanitize_sql
from app.schema_catalog import TABLE_CATALOG, get_table_schema_prompt, catalog_manager
from app.vector_store import vector_store
from app.llm_rotator import llm_client

logger = logging.getLogger("agent.core")

def _diagnose_column_error(err_str: str, current_sql: str) -> list[str]:
    advice = []
    if "UndefinedColumn" not in err_str and "does not exist" not in err_str:
        return advice
    col_match = re.search(r'column [\"\\\']?([a-zA-Z0-9_\.]+)[\"\\\']? does not exist', err_str)
    if col_match:
        missing = col_match.group(1)
        advice.append(f"- Database Error: Column '{missing}' DOES NOT EXIST in the referenced table.")
    catalog = catalog_manager.get_catalog()
    sql_lower = current_sql.lower()
    for t_name, info in catalog.items():
        short_tbl = info.get("table_name", t_name)
        if short_tbl.lower() in sql_lower:
            real_cols = catalog_manager.get_columns_for_table(short_tbl)
            if real_cols:
                advice.append(f"- Real valid columns for '{short_tbl}': {real_cols}")
    return advice

def _diagnose_syntax_errors(err_str: str) -> list[str]:
    advice = []
    if "operator does not exist: text ->>" in err_str or ("operator does not exist" in err_str and "->" in err_str):
        advice.append("- In PostgreSQL, column data type is TEXT. You MUST cast it: CAST(col AS json) ->> 'field' or col::json ->> 'field'.")
    if "UndefinedTable" in err_str:
        tbl_match = re.search(r'relation [\"\\\']?([a-zA-Z0-9_\.]+)[\"\\\']? does not exist', err_str)
        if tbl_match:
            advice.append(f"- Table '{tbl_match.group(1)}' does not exist. Remember multi-service schemas: qualify with 'public.<name>', 'us.<name>', or 'ls.<name>'.")
    if "must appear in the GROUP BY clause" in err_str:
        advice.append("- Every non-aggregated column in the SELECT list must appear in the GROUP BY clause.")
    return advice

def build_sql_error_diagnostic(err_str: str, current_sql: str) -> str:
    """Dynamically inspects PostgreSQL errors and injects exact introspected table/column guidance."""
    diagnostics = _diagnose_column_error(err_str, current_sql) + _diagnose_syntax_errors(err_str)
    if diagnostics:
        return "DIAGNOSTIC ADVICE FROM DATABASE CATALOG:\n" + "\n".join(diagnostics)
    return ""

UNIVERSAL_SYSTEM_PROMPT = """You are an intelligent, versatile AI Data Specialist for the Markazi ERP / Order Management / Inventory / Warehouse / Courier system.
Given the user's message and the dynamically introspected PostgreSQL schema, determine the appropriate response:

1. GREETINGS & CASUAL CONVERSATION:
- If the user says a greeting (e.g. hi, hello, salam, how are you, etc.), thanks, or asks general questions about Markazi or what you can do, respond conversationally, politely, and warmly in 1-2 natural sentences as a helpful data assistant.
- Do NOT generate any SQL query for greetings or casual conversation.

2. DATABASE QUESTIONS (SQL GENERATION):
- Write a valid, optimized, read-only PostgreSQL SELECT query based strictly on the provided schema.
- Schema Rules: Use ONLY tables and columns explicitly present in the provided schema context. Never invent tables or columns.
- Quoting Identifiers: PostgreSQL is case-sensitive for quoted identifiers. Always wrap column or table names in double quotes ("columnName", "tableName") if they contain uppercase letters (camelCase) or match SQL reserved keywords (e.g. "order", "orderNo", "inventorySourceOrderNo", "orderSource", "paymentMethod", "finalAmount", "onHand", "channelName", "courierName").
- Foreign Keys: Strictly follow the relationships defined in the schema for JOIN operations.
- Case-Insensitivity: Text matching with '=' in PostgreSQL is case-sensitive. Always use ILIKE (e.g. column ILIKE '%term%') or LOWER(column) / UPPER(column) for text filters to avoid case mismatches.
- Enum Types: If filtering an ENUM column, cast it to text when using ILIKE (column::text ILIKE '...') or match against the allowed enum values listed in the schema.
- Aggregations: For questions asking for totals, counts, averages, or top/bottom items, use aggregate functions (COUNT, SUM, AVG, MAX, MIN) with proper GROUP BY.
- Limit: ABSOLUTELY NEVER add a LIMIT clause unless the user explicitly requested a specific number of items (e.g. 'top 5', 'first 10'). Always select ALL matching rows so complete data is returned without any truncation.
- Typo Tolerance: Naturally infer user intent and map misspelled or colloquial terms to the corresponding schema items.
- Formatting: Output the SQL query strictly enclosed inside a ```sql ... ``` code block. Do NOT include explanations outside the code block.

3. MARKAZI MULTI-SERVICE BUSINESS RULES & ARCHITECTURE:
- Unified Databases (FDW): Three linked services:
  * IS (Inventory & Operations Hub - schema 'public'): product, product_variant, stock, location, "order", order_item, courier, channel, company, journal.
  * US (User Management & RBAC - schema 'us'): us.users, us.roles, us.permissions, us.role_permissions, us.widgets, us.theme_settings.
  * LS (License & Billing - schema 'ls'): ls.license, ls.invoice, ls.service_providers.
- Search Path & Schema Qualification: Search path is set to 'public, us, ls'. You can use us.users or users, ls.license or license, public.location or location, public."order" or "order". Schema qualification is recommended for clarity.
- User to Warehouse/Store Link: us.users."locationId" = public.location.id (connects staff/users to assigned physical warehouse or store location).
  Example: SELECT u.name, u.email, l.name AS warehouse_name FROM us.users u JOIN public.location l ON u."locationId" = l.id.
- User to Roles Link: us.users."roleId" = us.roles.id.
- License & Quotas: ls.license.configuration contains JSON limits (allowed warehouses, allowed staff, order processing quota, ERP, channel/courier addons).
- Invoices & Billing: ls.invoice tracks subscription bills and payment statuses.
- product vs product_variant: 'product' is the master record (e.g. Nike Shoes); 'product_variant' is the actual SKU/sellable item (e.g. Nike Shoes Black Size 42).
- Order Products & Who Ordered: "order" -> order_item -> product_variant -> (LEFT JOIN) product.
  CRITICAL: ALWAYS use LEFT JOIN for public.product because product_variant.product can be NULL for standalone variants!
  Always select: COALESCE(product.title, product_variant.title, product_variant.sku) AS product_name.
  Always select: COALESCE("order"."customerName", "order"."createdByName") AS ordered_by_name, "order"."orderNo".
- Order History: For order timeline events, use 'order_activity'; for current status, use "order"."status".
- Price Hierarchy: product_variant -> product_price -> price_list.
- Courier & Shipping: "order" -> courier -> courier_person.
- Channels & Integrations: "order" -> channel -> partner.
- Net Sales / Actual Revenue: Exclude cancelled and returned orders:
  WHERE "order"."status"::text NOT IN ('CANCELLED', 'RETURNED_BY_CUSTOMER', 'RETURNED_BY_COURIER')
- Completed Orders: "order"."status"::text = 'DELIVERED'.
- In-Progress Orders: "order"."status"::text IN ('CONFIRMED', 'PACKING', 'PACKED', 'DISPATCHED').
- Excluded Tables: Do NOT query 'system_log' or 'migration_table' unless specifically asked.
"""

SYNTHESIZE_SYSTEM_PROMPT = """You are a professional, helpful, and friendly AI Business Specialist.
Analyze the database query results and provide a natural, human-like response in clear, simple English (or polite Roman Urdu if the user spoke in Roman Urdu).

CRITICAL PROFESSIONAL RULES:
1. HUMAN TONE: Speak naturally like a knowledgeable colleague. Avoid robotic phrasing like "Based on the SQL query executed", "Here is the result", or "According to the table".
2. ABSOLUTELY NO TABLES: Never format output into markdown tables (| --- | --- |). The user strictly forbids tables.
3. FORMATTING: Present the answer directly in clear sentences or clean, concise bullet points.
4. EXACT NUMBERS: State exact counts, sales amounts, dates, and names naturally within the sentences.
5. NO TECHNICAL JARGON: Do not quote raw SQL syntax, code blocks, or raw database column names. Use natural business language.
6. CRISP & DIRECT: Be direct, polite, and helpful without unnecessary filler.
7. COMPLETE DATA INTEGRITY (NO LIMITS): Always present ALL data records completely. Never truncate, never skip records, and never write 'the remaining records also fall under...' or 'and more'. The user insists on complete, untruncated data.
8. CHUNKED PRESENTATION FOR LARGE DATA: When presenting multiple records (>6 items), DO NOT dump a continuous unorganized wall of bullets. Group and organize the response into clear, logical CHUNKS / SECTIONS using markdown headers (### ...). Group by Location/Warehouse, Status/Priority, Category, or Batches. Under each chunk, list items in clean, readable bullets. Start with a crisp 1-2 sentence executive summary.
"""

def extract_sql_query(raw_text: str) -> Optional[str]:
    """Extracts SQL code block from LLM response if present."""
    match = re.search(r"```(?:sql)?\s*([\s\S]*?)\s*```", raw_text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    trimmed = raw_text.strip().rstrip(";")
    upper = trimmed.upper()
    if upper.startswith("SELECT ") or upper.startswith("WITH "):
        return trimmed
    return None

def serialize_row(val: Any) -> Any:
    """Helper to convert non-serializable objects (Decimal, datetime) to JSON-friendly types."""
    if isinstance(val, Decimal):
        return float(val)
    elif isinstance(val, (datetime,)):
        return val.isoformat()
    return val

def compute_data_summary(rows: list[dict], columns: list[str]) -> dict:
    """Computes statistical metrics (sum, avg, min, max) across ALL returned records."""
    if not rows:
        return {"total_count": 0, "stats": {}}
    stats = {}
    for col in columns:
        vals = [r[col] for r in rows if isinstance(r.get(col), (int, float))]
        if vals:
            stats[col] = {
                "sum": round(sum(vals), 2),
                "avg": round(sum(vals) / len(vals), 2),
                "min": min(vals),
                "max": max(vals)
            }
    return {"total_count": len(rows), "stats": stats}

def _is_id_column(col: str) -> bool:
    c = col.lower()
    return c in ("id", "sourceid", "source_id") or c.endswith("id")

def _find_label_column(rows: list[dict], columns: list[str]) -> Optional[str]:
    for col in columns:
        if _is_id_column(col):
            continue
        sample_vals = [r.get(col) for r in rows[:5] if r.get(col) is not None]
        if sample_vals and all(isinstance(v, str) for v in sample_vals):
            return col
    for col in columns:
        sample_vals = [r.get(col) for r in rows[:5] if r.get(col) is not None]
        if sample_vals and all(isinstance(v, str) for v in sample_vals):
            return col
    return None

def _find_numeric_column(rows: list[dict], columns: list[str]) -> Optional[str]:
    for col in columns:
        if _is_id_column(col):
            continue
        sample_vals = [r.get(col) for r in rows[:5] if r.get(col) is not None]
        if sample_vals and all(isinstance(v, (int, float)) for v in sample_vals):
            return col
    return None

def _determine_chart_type(label_col: str, row_count: int) -> str:
    lbl_lower = label_col.lower()
    time_terms = ("month", "date", "day", "created", "time", "year")
    if any(term in lbl_lower for term in time_terms):
        return "line"
    category_terms = ("status", "type", "channel")
    if row_count <= 5 and any(term in lbl_lower for term in category_terms):
        return "doughnut"
    return "bar"

def extract_chart_data(rows: list[dict], columns: list[str]) -> Optional[dict]:
    """Automatically constructs visual chart parameters (bar, line, doughnut) for comparative or time-series data."""
    if len(rows) < 2:
        return None
    label_col = _find_label_column(rows, columns)
    numeric_col = _find_numeric_column(rows, columns)
    if not (label_col and numeric_col):
        return None

    chart_rows = rows[:100]
    chart_type = _determine_chart_type(label_col, len(chart_rows))
    return {
        "type": chart_type,
        "title": f"{numeric_col.replace('_', ' ').title()} by {label_col.replace('_', ' ').title()}",
        "labels": [str(r.get(label_col, '')) for r in chart_rows],
        "label_name": label_col,
        "value_name": numeric_col,
        "data": [float(r.get(numeric_col) or 0) for r in chart_rows]
    }

def build_synthesis_prompt(user_question: str, serialized_rows: list[dict], data_summary: dict, history: Optional[list[dict]]) -> str:
    total_count = len(serialized_rows)
    synth_history = ""
    if history:
        clean_recent = [h for h in history[-4:] if isinstance(h, dict) and h.get("content")]
        if clean_recent:
            synth_history = "Recent Context:\n" + "\n".join([
                f"- {'User' if h['role'] == 'user' else 'Assistant'}: {h['content'][:150]}"
                for h in clean_recent
            ]) + "\n\n"

    if total_count <= 25:
        data_section = f"Complete Matching Records ({total_count} total records):\n{json.dumps(serialized_rows, separators=(',', ':'))}"
        instruction_text = """1. COMPLETE ITEM DETAIL: Present all matching records provided above in clear, professional sentences or clean bullet points.
2. CHUNKED PRESENTATION: If more than 5 items, group them into logical CHUNKS / SECTIONS using markdown headers (### ...) by Location, Status, or Category.
3. State exact numbers, names, and quantities clearly."""
    else:
        top_sample = serialized_rows[:20]
        data_section = f"""Total Matching Records Found in Database: {total_count}
Pre-computed Statistical Summary across ALL {total_count} records:
{json.dumps(data_summary, indent=2)}

Top Highlight Records (Sample of first 20 records):
{json.dumps(top_sample, separators=(',', ':'))}"""

        instruction_text = f"""1. LARGE DATASET EXECUTIVE SUMMARY: The query returned {total_count} total records.
2. Provide a high-impact, professional Executive Summary:
   - Clearly state the total count ({total_count} records found in database).
   - Summarize key financial, product, or volume figures from the computed summary.
   - Present the top highlight records grouped into logical CHUNKS / SECTIONS using markdown headers (### ...) with clean bullet points.
   - Explicitly inform the user: 'The complete dataset of all {total_count} records is available in the interactive Data Table below and can be downloaded as CSV.'"""

    return f"""{synth_history}User Question: "{user_question}"
Total Matching Records in Database: {total_count}

{data_section}

INSTRUCTIONS FOR ANSWER:
{instruction_text}
- Speak like a helpful human business specialist. Do NOT output raw SQL code, raw unformatted column names, or markdown pipe tables."""

class QueryContext:
    def __init__(
        self,
        relevant_tables: list[str],
        matched_entities: list[dict],
        schema_context: str,
        user_prompt: str,
        messages: list[dict[str, str]],
    ):
        self.relevant_tables = relevant_tables
        self.matched_entities = matched_entities
        self.schema_context = schema_context
        self.user_prompt = user_prompt
        self.messages = messages

DEFAULT_FALLBACK_REPLY = (
    "Main aapka sawal samajh nahi paya ya mutaliqa data nahi mil saka. "
    "Barah-e-karam apna sawal thora wazeh karein ya dobara poochiye."
)

def _select_schema_tables(relevant_tables: list[str]) -> list[str]:
    selected_tables = []
    for t in relevant_tables:
        info = TABLE_CATALOG.get(t)
        t_name = info.get("table_name", t) if info else t
        if t_name not in selected_tables:
            selected_tables.append(t_name)

    core_fallback = ["order", "order_item", "product", "product_variant", "stock", "location", "users", "roles", "license"]
    for c in core_fallback:
        if len(selected_tables) >= 8:
            break
        if c not in selected_tables and c in TABLE_CATALOG:
            selected_tables.append(c)
    return selected_tables[:8]

def _format_entity_context(matched_entities: list[dict]) -> str:
    if not matched_entities:
        return ""
    return "Matched Database Entities:\n" + "\n".join(
        [f"- {e['type'].upper()} '{e['name']}' (ID: {e['id']})" for e in matched_entities]
    )

def _format_history_context(history: Optional[list[dict]]) -> str:
    if not history:
        return ""
    clean_history = [
        h for h in history[-6:]
        if isinstance(h, dict) and h.get("content") and h.get("role") in ("user", "assistant")
    ]
    if not clean_history:
        return ""
    turns = []
    for h in clean_history:
        turn_str = f"{'User' if h['role'] == 'user' else 'Assistant'}: {h['content'][:250]}"
        if h.get("sql"):
            turn_str += f"\n  [Executed SQL]: {h['sql']}"
        turns.append(turn_str)
    return "Recent Conversation History:\n" + "\n".join(turns) + "\n"

def _build_query_context(user_question: str, history: Optional[list[dict]] = None) -> QueryContext:
    relevant_tables = vector_store.search_relevant_tables(user_question, top_k=8)
    matched_entities = vector_store.search_entities(user_question, top_k=8)

    selected_tables = _select_schema_tables(relevant_tables)
    schema_context = get_table_schema_prompt(selected_tables)
    entity_context = _format_entity_context(matched_entities)
    history_context = _format_history_context(history)

    user_prompt = f"""Available Database Schema Context:
{schema_context}

{entity_context}

{history_context}
Current User Input: "{user_question}"

INSTRUCTIONS:
1. If this is a greeting or general inquiry, respond conversationally.
2. If this is a data question, generate the PostgreSQL query in ```sql ... ```.
3. If this is a follow-up to a previous question, reuse or extend the previous [Executed SQL]."""

    messages = [
        {"role": "system", "content": UNIVERSAL_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]
    return QueryContext(relevant_tables, matched_entities, schema_context, user_prompt, messages)

def _build_failure_message(err_str: str, ctx: QueryContext) -> str:
    table_summary = ", ".join(ctx.relevant_tables[:4]) if ctx.relevant_tables else "database"
    return (
        f"Database query execute nahi ho saki: {err_str}.\n\n"
        f"**Suggestions:**\n"
        f"- Mutaliqa tables ({table_summary}) mein requested fields direct match nahi huin.\n"
        f"- Aap specific filters (e.g. warehouse name, specific SKU ya date range) mention kar ke dobara pooch sakte hain."
    )

def _format_conversational_response(reply_text: str, ctx: QueryContext) -> dict[str, Any]:
    return {
        "answer": reply_text,
        "sql": "",
        "columns": [],
        "rows": [],
        "row_count": 0,
        "duration_ms": 0,
        "relevant_tables": ctx.relevant_tables,
        "entities": ctx.matched_entities,
        "chart": None,
        "error": None
    }

def _format_security_error_response(sql_to_run: str, error_msg: str, ctx: QueryContext) -> dict[str, Any]:
    return {
        "answer": f"Query could not be executed due to security rules: {error_msg}",
        "sql": sql_to_run,
        "columns": [],
        "rows": [],
        "row_count": 0,
        "duration_ms": 0,
        "relevant_tables": ctx.relevant_tables,
        "entities": ctx.matched_entities,
        "chart": None,
        "error": error_msg
    }

def _prepare_synthesis_data(exec_result: dict, user_question: str, history: Optional[list[dict]]) -> tuple[list[dict], list[str], Optional[dict], list[dict[str, str]]]:
    columns = exec_result.get("columns", [])
    raw_rows = exec_result.get("rows", [])
    serialized_rows = [{k: serialize_row(v) for k, v in row.items()} for row in raw_rows]
    data_summary = compute_data_summary(serialized_rows, columns)
    chart_data = extract_chart_data(serialized_rows, columns)
    summary_prompt = build_synthesis_prompt(user_question, serialized_rows, data_summary, history)
    synth_messages = [
        {"role": "system", "content": SYNTHESIZE_SYSTEM_PROMPT},
        {"role": "user", "content": summary_prompt}
    ]
    return serialized_rows, columns, chart_data, synth_messages

async def _stream_tokens_or_fallback(synth_messages: list[dict], serialized_rows: list[dict]):
    token_count = 0
    async for token in llm_client.stream_chat_completion(synth_messages, temperature=0.2):
        if token:
            token_count += 1
            yield {"event": "token", "data": json.dumps({"token": token})}

    if token_count == 0:
        logger.warning("Stream produced 0 tokens, falling back to direct synthesis...")
        try:
            fallback_answer = await llm_client.generate_chat_completion(synth_messages, temperature=0.2)
            if fallback_answer and fallback_answer.strip():
                yield {"event": "token", "data": json.dumps({"token": fallback_answer.strip()})}
            else:
                yield {"event": "token", "data": json.dumps({"token": f"Aapke sawal ke mutabiq {len(serialized_rows)} records mil gaye hain. Tafseelat Data Table aur CSV export mein mojood hain."})}
        except Exception as synth_err:
            logger.error(f"Fallback synthesis error: {synth_err}")
            yield {"event": "token", "data": json.dumps({"token": f"Aapka data query kamyabi se execute ho gaya hai ({len(serialized_rows)} records). Interactive table mein check karein."})}

class ChatbotAgent:
    async def _attempt_sql_fix(self, current_sql: str, err_str: str, user_prompt: str) -> str:
        diagnostic_hint = build_sql_error_diagnostic(err_str, current_sql)
        hint_section = f"\n{diagnostic_hint}\n" if diagnostic_hint else ""
        fix_prompt = (
            f"The PostgreSQL query failed with error: {err_str}\n"
            f"Faulty SQL: {current_sql}\n"
            f"{hint_section}"
            f"Fix the query using the schema provided above. "
            f"Ensure correct table and column names, proper double quotes on identifiers, "
            f"and remember ls.license.configuration is TEXT (use CAST(lic.configuration AS json) ->> 'key'). "
            f"Output ONLY the corrected SQL in ```sql ... ```."
        )
        try:
            fix_messages = [
                {"role": "system", "content": UNIVERSAL_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": f"```sql\n{current_sql}\n```"},
                {"role": "user", "content": fix_prompt}
            ]
            fix_output = await llm_client.generate_chat_completion(fix_messages, temperature=0.05)
            corrected_sql = extract_sql_query(fix_output)
            if corrected_sql:
                valid, sanitized_sql_fixed, _ = validate_and_sanitize_sql(corrected_sql)
                if valid:
                    return sanitized_sql_fixed
        except Exception as fix_err:
            logger.warning(f"Self-correction LLM call failed: {fix_err}")
        return current_sql

    async def _execute_sql_with_retry(self, initial_sql: str, user_prompt: str, max_retries: int = 2) -> tuple[bool, Optional[dict], str, str]:
        current_sql = initial_sql
        err_str = ""
        for attempt in range(max_retries + 1):
            try:
                exec_result = await db_manager.execute_query(current_sql)
                if exec_result.get("success"):
                    return True, exec_result, current_sql, ""
            except Exception as e:
                err_str = str(e)
                logger.warning(f"SQL execution error on attempt {attempt+1}: {err_str}")
                if attempt < max_retries:
                    current_sql = await self._attempt_sql_fix(current_sql, err_str, user_prompt)
        return False, None, current_sql, err_str

    async def process_query(self, user_question: str, history: Optional[list[dict]] = None) -> dict[str, Any]:
        """
        Universal Hybrid Pipeline with Conversation History:
        1. Semantic Retrieval of relevant schema & entities from Vector Store
        2. Contextual History integration (including prior SQL) for follow-up questions
        3. LLM evaluates intent: conversational greeting vs database query
        4. If database query: AST security validation, execution, self-correction, pre-aggregation, synthesis
        5. If conversational: returns friendly direct answer
        """
        logger.info(f"Processing user question: {user_question}")
        ctx = _build_query_context(user_question, history)

        llm_output = await llm_client.generate_chat_completion(ctx.messages, temperature=0.1)
        sql_to_run = extract_sql_query(llm_output)

        if not sql_to_run:
            logger.info("Model responded conversationally without SQL.")
            reply_text = llm_output.strip() if llm_output and llm_output.strip() else DEFAULT_FALLBACK_REPLY
            return _format_conversational_response(reply_text, ctx)

        is_valid, sanitized_sql, error_msg = validate_and_sanitize_sql(sql_to_run)
        if not is_valid:
            return _format_security_error_response(sql_to_run, error_msg, ctx)

        success, exec_result, final_sql, err_str = await self._execute_sql_with_retry(sanitized_sql, ctx.user_prompt, max_retries=2)
        if not success or not exec_result:
            fail_msg = _build_failure_message(err_str, ctx)
            return {
                "answer": fail_msg,
                "sql": final_sql,
                "columns": [],
                "rows": [],
                "row_count": 0,
                "duration_ms": 0,
                "relevant_tables": ctx.relevant_tables,
                "entities": ctx.matched_entities,
                "chart": None,
                "error": err_str
            }

        serialized_rows, columns, chart_data, synth_messages = _prepare_synthesis_data(exec_result, user_question, history)
        natural_answer = await llm_client.generate_chat_completion(synth_messages, temperature=0.2)

        return {
            "answer": natural_answer,
            "sql": final_sql,
            "columns": columns,
            "rows": serialized_rows,
            "row_count": len(serialized_rows),
            "duration_ms": exec_result.get("duration_ms", 0),
            "relevant_tables": ctx.relevant_tables,
            "entities": ctx.matched_entities,
            "chart": chart_data,
            "error": None
        }

    async def process_query_stream(self, user_question: str, history: Optional[list[dict]] = None):
        """
        Streaming execution pipeline emitting SSE events step-by-step:
        stage (retrieval -> sql -> synthesizing) followed by token stream.
        """
        yield {"event": "stage", "data": json.dumps({"stage": "retrieval", "message": "Searching database schema & entities..."})}

        ctx = _build_query_context(user_question, history)
        llm_output = await llm_client.generate_chat_completion(ctx.messages, temperature=0.1)
        sql_to_run = extract_sql_query(llm_output)

        if not sql_to_run:
            reply_text = llm_output.strip() if llm_output and llm_output.strip() else DEFAULT_FALLBACK_REPLY
            yield {"event": "stage", "data": json.dumps({"stage": "synthesizing", "message": "Replying..."})}
            yield {"event": "token", "data": json.dumps({"token": reply_text})}
            yield {"event": "done", "data": json.dumps({"sql": "", "columns": [], "row_count": 0, "chart": None})}
            return

        is_valid, sanitized_sql, error_msg = validate_and_sanitize_sql(sql_to_run)
        if not is_valid:
            yield {"event": "token", "data": json.dumps({"token": f"Security restriction: {error_msg}"})}
            yield {"event": "done", "data": json.dumps({"sql": sql_to_run, "columns": [], "row_count": 0, "chart": None})}
            return

        yield {"event": "stage", "data": json.dumps({"stage": "sql", "message": "Executing PostgreSQL query...", "sql": sanitized_sql})}

        success, exec_result, final_sql, err_str = await self._execute_sql_with_retry(sanitized_sql, ctx.user_prompt, max_retries=2)
        if not success or not exec_result:
            fail_msg = _build_failure_message(err_str, ctx)
            yield {"event": "token", "data": json.dumps({"token": fail_msg})}
            yield {"event": "done", "data": json.dumps({"sql": final_sql, "columns": [], "row_count": 0, "chart": None})}
            return

        serialized_rows, columns, chart_data, synth_messages = _prepare_synthesis_data(exec_result, user_question, history)

        yield {"event": "stage", "data": json.dumps({"stage": "synthesizing", "message": "Synthesizing answer..."})}

        async for item in _stream_tokens_or_fallback(synth_messages, serialized_rows):
            yield item

        yield {"event": "done", "data": json.dumps({
            "sql": final_sql,
            "columns": columns,
            "rows": serialized_rows,
            "row_count": len(serialized_rows),
            "duration_ms": exec_result.get("duration_ms", 0),
            "relevant_tables": ctx.relevant_tables,
            "entities": ctx.matched_entities,
            "chart": chart_data
        })}

agent = ChatbotAgent()

