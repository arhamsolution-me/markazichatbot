# Markazi AI Chatbot Microservice - API Documentation

This document explains all available backend APIs for the Markazi AI Chatbot Microservice in clear, simple English without any tables.

The default microservice port is **6070**.

---

## 1. Core Input & Output APIs (Chat & Query Endpoints)

These are the primary APIs used by client applications (web, mobile, or third-party services) to communicate with the chatbot.

### 1.1 Standard Chat API (POST `/api/chat`)

* **Purpose:**
  This is the main synchronous input/output API. You send a user question in English or Roman Urdu, and the chatbot generates a read-only PostgreSQL query, executes it safely across the databases, and returns a natural human-like answer along with the raw database rows and optional chart data in a single JSON response.

* **HTTP Method:** `POST`
* **URL:** `http://<SERVER_IP>:6070/api/chat`

* **Request Headers:**
  * `Content-Type: application/json`
  * `Authorization: Bearer <API_TOKEN>` (Optional: only needed if CHAT_API_TOKEN is enabled in .env)

* **Input Body (JSON):**
  * `message` (string, required): The user's question or message.
  * `history` (array of objects, optional): Previous chat messages for context.
    * `role` (string): Either "user" or "assistant".
    * `content` (string): Text content of the previous message.
    * `sql` (string, optional): Previously executed SQL query if applicable.

  Example Input:
  ```json
  {
    "message": "Which warehouse has the highest onHand stock?",
    "history": []
  }
  ```

* **Output Body (JSON):**
  * `answer` (string): Natural language business response synthesized by the AI.
  * `sql` (string): Safe PostgreSQL query generated and executed by the backend.
  * `columns` (array of strings): Column headers returned from the database.
  * `rows` (array of objects): Complete records retrieved from the database.
  * `row_count` (integer): Total number of rows returned.
  * `duration_ms` (number): Time taken by the database query in milliseconds.
  * `relevant_tables` (array of strings): Tables retrieved from dynamic schema search.
  * `entities` (array of objects): Fuzzy or exact matched entities (products, warehouses, etc.).
  * `chart` (object or null): Pre-configured chart parameters (type, labels, values) for rendering Bar, Line, or Doughnut graphs on the frontend.
  * `error` (string or null): Error description if any issue occurred, otherwise null.

  Example Output:
  ```json
  {
    "answer": "The Main Warehouse currently holds the highest inventory with 12,450 units across all product variants.",
    "sql": "SELECT l.name AS warehouse_name, SUM(s.\"onHand\") AS total_stock FROM public.location l JOIN public.stock s ON s.location = l.id GROUP BY l.name ORDER BY total_stock DESC;",
    "columns": ["warehouse_name", "total_stock"],
    "rows": [
      {
        "warehouse_name": "Main Warehouse",
        "total_stock": 12450
      },
      {
        "warehouse_name": "Lahore Depot",
        "total_stock": 8320
      }
    ],
    "row_count": 2,
    "duration_ms": 14.2,
    "relevant_tables": ["location", "stock"],
    "entities": [],
    "chart": {
      "type": "bar",
      "title": "Total Stock by Warehouse Name",
      "labels": ["Main Warehouse", "Lahore Depot"],
      "label_name": "warehouse_name",
      "value_name": "total_stock",
      "data": [12450, 8320]
    },
    "error": null
  }
  ```

---

### 1.2 Real-Time Streaming Chat API (POST `/api/chat/stream`)

* **Purpose:**
  This endpoint streams the response word-by-word using Server-Sent Events (SSE). It is ideal for frontend UIs that want a real-time typewriter effect and live step-by-step progress updates (showing when it is searching schema, running SQL, and generating text).

* **HTTP Method:** `POST`
* **URL:** `http://<SERVER_IP>:6070/api/chat/stream`

* **Request Headers:**
  * `Content-Type: application/json`
  * `Accept: text/event-stream`
  * `Authorization: Bearer <API_TOKEN>` (Optional)

* **Input Body (JSON):**
  Same as the standard chat endpoint:
  ```json
  {
    "message": "Total delivered orders kitne hain?",
    "history": []
  }
  ```

* **Output Stream Events:**
  The server keeps the HTTP connection open and emits sequential events:

  1. `event: stage`
     Emits the current progress stage of the backend pipeline:
     * Stage "retrieval": Searching vector catalog for relevant tables and entities.
     * Stage "sql": Executing PostgreSQL query.
     * Stage "synthesizing": Generating natural language answer.
     Example:
     ```http
     event: stage
     data: {"stage": "sql", "message": "Executing PostgreSQL query...", "sql": "SELECT COUNT(*) FROM public.\"order\" WHERE \"status\"::text = 'DELIVERED';"}
     ```

  2. `event: token`
     Streams individual tokens of the answer in real time:
     ```http
     event: token
     data: {"token": "Currently"}

     event: token
     data: {"token": ", there are 1,450"}

     event: token
     data: {"token": " delivered orders."}
     ```

  3. `event: done`
     Emits the final completed metadata package containing SQL, columns, rows, row count, and chart object:
     ```http
     event: done
     data: {"sql": "SELECT COUNT(*) FROM public.\"order\"...", "columns": ["count"], "rows": [{"count": 1450}], "row_count": 1, "chart": null}
     ```

---

## 2. Diagnostics, Health, and Synchronization APIs

### 2.1 System Health and Multi-Database Stats (GET `/api/stats`)

* **Purpose:**
  Provides a health check and detailed summary of the connected multi-service databases (Inventory Hub, User Management, and Licensing) connected via PostgreSQL Foreign Data Wrapper (FDW), as well as active Groq keys and configured LLM models.

* **HTTP Method:** `GET`
* **URL:** `http://<SERVER_IP>:6070/api/stats`

* **Input:** None (No query parameters or request body required).

* **Output Body (JSON):**
  * `status`: "healthy"
  * `database`: Name of the primary database ("markazi_qa_is").
  * `linked_services`: Breakdown of the 3 integrated services:
    * `is`: Inventory & Operations Hub (schema "public") table count.
    * `us`: User Management & RBAC Service (schema "us") table count.
    * `ls`: License & Billing Service (schema "ls") table count.
  * `total_tables_count`: Total introspected tables across all services.
  * `available_tables`: Array of all accessible table names.
  * `tables_by_schema`: Dictionary grouping tables by schema name.
  * `groq_keys_count`: Number of active Groq API keys in the key rotator pool.
  * `model`: Current active Groq model name.

  Example Output:
  ```json
  {
    "status": "healthy",
    "database": "markazi_qa_is",
    "linked_services": {
      "is": {
        "name": "Inventory & Operations Hub",
        "schema": "public",
        "tables_count": 22
      },
      "us": {
        "name": "User Management & RBAC Service",
        "schema": "us",
        "tables_count": 7
      },
      "ls": {
        "name": "License & Billing Service",
        "schema": "ls",
        "tables_count": 4
      }
    },
    "total_tables_count": 33,
    "available_tables": ["order", "product", "location", "us.users", "us.roles", "ls.license"],
    "tables_by_schema": {
      "public": ["order", "product", "location"],
      "us": ["users", "roles"],
      "ls": ["license", "invoice"]
    },
    "groq_keys_count": 12,
    "model": "openai/gpt-oss-120b"
  }
  ```

---

### 2.2 On-Demand Entity Sync (POST `/api/sync`)

* **Purpose:**
  Triggers an immediate background synchronization of database entities (channels, couriers, active warehouse locations, products, user accounts, and roles) into the Qdrant Vector Store. Use this endpoint whenever new products or warehouses are added to the database so the AI recognizes them instantly without restarting the server.

* **HTTP Method:** `POST`
* **URL:** `http://<SERVER_IP>:6070/api/sync`

* **Input:** None (No body required).

* **Output Body (JSON):**
  * `status` (string): "success"
  * `message` (string): "Entities re-synchronized with Vector Store."

  Example Output:
  ```json
  {
    "status": "success",
    "message": "Entities re-synchronized with Vector Store."
  }
  ```

---

### 2.3 Microservice Root Status (GET `/`)

* **Purpose:**
  Simple, lightweight health check endpoint for API gateways, load balancers, or uptime monitors to check if the microservice is alive.

* **HTTP Method:** `GET`
* **URL:** `http://<SERVER_IP>:6070/`

* **Input:** None.

* **Output Body (JSON):**
  * `service` (string): "Markazi AI Chatbot Core Microservice"
  * `status` (string): "healthy"
  * `version` (string): "1.0.0"

  Example Output:
  ```json
  {
    "service": "Markazi AI Chatbot Core Microservice",
    "status": "healthy",
    "version": "1.0.0"
  }
  ```
