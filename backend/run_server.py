import os
import sys
import asyncio
from dotenv import load_dotenv

load_dotenv()

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "6070"))
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=False
    )
