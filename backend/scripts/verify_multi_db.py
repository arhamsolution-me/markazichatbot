import os
from pathlib import Path
import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env", override=True)

raw_url = os.getenv("MARKAZI_DB_URL", "")
if not raw_url:
    raise ValueError("MARKAZI_DB_URL environment variable must be set.")
dsn = raw_url.replace("postgresql+psycopg://", "postgresql://")

with psycopg.connect(dsn) as conn:
    conn.execute("SET search_path TO public, us, ls")
    checks = [
        'SELECT COUNT(*) FROM public."order"',
        'SELECT COUNT(*) FROM us.users',
        'SELECT COUNT(*) FROM ls.license',
        'SELECT COUNT(*) FROM public.location',
        'SELECT COUNT(*) FROM public.product',
    ]
    for q in checks:
        n = conn.execute(q).fetchone()[0]
        print(f"{q}: {n}")
    rows = conn.execute(
        """
        SELECT n.nspname, COUNT(*)
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname IN ('public', 'us', 'ls') AND c.relkind IN ('r', 'f')
        GROUP BY 1 ORDER BY 1
        """
    ).fetchall()
    print("tables:", rows)
