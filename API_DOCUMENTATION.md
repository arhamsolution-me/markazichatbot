# Markazi AI Chatbot - API Documentation

Yeh document Markazi AI Chatbot backend ki tamam APIs ki mukammal tafseel, unka maqsad (purpose), request format aur response structure faraham karta hai.

---

## 1. Overview Table

| Method | Endpoint | Naam / Purpose | Format |
|---|---|---|---|
| `POST` | `/api/chat` | Standard Chat & Data Query (Single JSON response) | JSON |
| `POST` | `/api/chat/stream` | Real-Time Streaming Chat (Typewriter effect + Pipeline stages) | SSE (`text/event-stream`) |
| `GET` | `/api/stats` | System Health, Multi-Database Schemas aur Model Stats | JSON |
| `POST` | `/api/sync` | Manual Database Entities Sync to Vector DB (Qdrant) | JSON |
| `GET` | `/` | Microservice Health & Status Endpoint | JSON |

---

## 2. API Details

### 1. `POST /api/chat`
* **Matlab / Maqsad (Purpose):**
  * Yeh chatbot ka main communication endpoint hai.
  * Jab user koi aam sawal poochta hai (maslan: *"Hi"*, *"Salam"*, *"Aap kya kar sakte ho"*), yeh conversational jawab deta hai.
  * Jab user koi business ya database query karta hai (maslan: *"Total delivered orders kitne hain?"*, *"Lahore warehouse ka stock kitna hai?"*), yeh:
    1. Vector database se relevant tables aur entities dhundta hai.
    2. Read-only safe PostgreSQL SQL query generate karta hai.
    3. Query ko security check (AST validation) se pass karta hai.
    4. Database se data nikal kar natural summary, structured table rows aur visual chart data tayyar kar ke bhejta hai.

* **Headers:**
  ```http
  Content-Type: application/json
  Authorization: Bearer <API_TOKEN>   # (Optional - agar config mein enable ho)
  ```

* **Request Body:**
  ```json
  {
    "message": "Pichle 30 dinon ke delivered orders ka total batayein?",
    "history": [
      {
        "role": "user",
        "content": "Pichle sawal ka context...",
        "sql": "SELECT ... (optional agar pehle run hui ho)"
      }
    ]
  }
  ```

* **Response (JSON):**
  ```json
  {
    "answer": "Pichle 30 dinon mein kul 1,450 delivered orders record hue hain jinki majmooi maliyat...",
    "sql": "SELECT COUNT(*), SUM(\"finalAmount\") FROM public.\"order\" WHERE \"status\"::text = 'DELIVERED';",
    "columns": ["count", "sum"],
    "rows": [
      {
        "count": 1450,
        "sum": 2845000.00
      }
    ],
    "row_count": 1,
    "duration_ms": 14.85,
    "relevant_tables": ["order", "order_item", "location"],
    "entities": [],
    "chart": {
      "type": "bar",
      "title": "Delivered Orders",
      "labels": ["Delivered"],
      "label_name": "status",
      "value_name": "count",
      "data": [1450]
    },
    "error": null
  }
  ```

---

### 2. `POST /api/chat/stream`
* **Matlab / Maqsad (Purpose):**
  * Yeh real-time live streaming endpoint hai jisme frontend par **typewriter effect** chalta hai.
  * Isme Server-Sent Events (SSE) use hoty hain taake user ko pata chale backend is waqt kya kar raha hai (Tables dhoond raha hai, SQL chala raha hai, ya answer likh raha hai).

* **Headers:**
  ```http
  Content-Type: application/json
  Accept: text/event-stream
  ```

* **Emitted Events Stream:**
  1. **Stage Events (`event: stage`):**
     * Pipeline ki live progress batata hai:
     ```json
     {"stage": "retrieval", "message": "Searching database schema & entities..."}
     {"stage": "sql", "message": "Executing PostgreSQL query...", "sql": "SELECT ..."}
     {"stage": "synthesizing", "message": "Synthesizing answer..."}
     ```
  2. **Token Events (`event: token`):**
     * Answer ke lafz ba lafz (word by word) tokens bhejta hai:
     ```json
     {"token": "Pichle"}
     {"token": " 30 dinon"}
     ```
  3. **Done Event (`event: done`):**
     * Stream khatam hone par final structured data bhejta hai:
     ```json
     {
       "sql": "SELECT ...",
       "columns": ["orderNo", "finalAmount"],
       "rows": [...],
       "row_count": 25,
       "chart": {...}
     }
     ```

---

### 3. `GET /api/stats`
* **Matlab / Maqsad (Purpose):**
  * System ki overall health, active models, aur teeno linked Markazi databases ki live status check karne ke liye use hota hai.
  * Yeh batata hai ke PostgreSQL FDW ke zariye teeno services theek se judi hui hain ya nahi.

* **Response (JSON):**
  ```json
  {
    "status": "healthy",
    "database": "markazi_qa_is",
    "linked_services": {
      "is": {
        "name": "Inventory & Operations Hub",
        "database": "markazi_qa_is",
        "schema": "public",
        "tables_count": 34
      },
      "us": {
        "name": "User Management & RBAC Service",
        "database": "markazi_qa_us",
        "schema": "us",
        "tables_count": 8
      },
      "ls": {
        "name": "License & Billing Service",
        "database": "markazi_qa_ls",
        "schema": "ls",
        "tables_count": 5
      }
    },
    "total_tables_count": 47,
    "available_tables": ["order", "product", "us.users", "ls.license", ...],
    "tables_by_schema": {
      "public": ["order", "location", "product", ...],
      "us": ["users", "roles", "permissions", ...],
      "ls": ["license", "invoice", "service_providers"]
    },
    "groq_keys_count": 5,
    "model": "openai/gpt-oss-120b"
  }
  ```

---

### 4. `POST /api/sync`
* **Matlab / Maqsad (Purpose):**
  * On-demand entity synchronizer hai.
  * PostgreSQL database se tammam **Channels**, **Couriers**, **Locations (Warehouses/Stores)**, **Products**, **Users (Staff)** aur **Roles** ko fauran utha kar Qdrant Vector Store mein index/upsert karta hai.
  * **Faida:** Agar database mein koi naya product ya warehouse add kiya gaya ho toh server restart kiye baghair yeh API call karne se chatbot us naye item ko foran pehchanne lagta hai.

* **Response (JSON):**
  ```json
  {
    "status": "success",
    "message": "Entities re-synchronized with Vector Store."
  }
  ```

---

### 5. `GET /`
* **Matlab / Maqsad (Purpose):**
  * Microservice root health & status endpoint.
  * API gateway ya load balancers ko microservice ki availability check karne ke liye live JSON response faraham karta hai.
* **Response (JSON):**
  ```json
  {
    "service": "Markazi AI Chatbot Core Microservice",
    "status": "healthy",
    "version": "1.0.0"
  }
  ```
