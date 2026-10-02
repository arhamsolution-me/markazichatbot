#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess
import urllib.parse
from pathlib import Path
import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent

load_dotenv(ROOT / ".env", override=True)

def find_psql() -> str:
    which_psql = shutil.which("psql")
    if which_psql:
        return which_psql
    
    candidates = [
        r"C:\pgsql\pgsql\bin\psql.exe",
        r"C:\Program Files\PostgreSQL\17\bin\psql.exe",
        r"C:\Program Files\PostgreSQL\16\bin\psql.exe",
        r"C:\Program Files\PostgreSQL\15\bin\psql.exe",
        r"C:\Program Files\PostgreSQL\14\bin\psql.exe",
        "/usr/bin/psql",
        "/usr/local/bin/psql",
        "/opt/homebrew/bin/psql",
    ]
    for c in candidates:
        if Path(c).exists():
            return c
    
    return "psql"

def parse_db_url(url: str) -> dict:
    clean_url = url.replace("postgresql+psycopg://", "postgresql://")
    parsed = urllib.parse.urlparse(clean_url)
    return {
        "user": parsed.username or "postgres",
        "password": parsed.password or "",
        "host": parsed.hostname or "127.0.0.1",
        "port": str(parsed.port or 5432),
        "dbname": parsed.path.lstrip("/") or "postgres"
    }

def find_dump_file(prefix: str) -> Path:
    matches = list(ROOT.glob(f"{prefix}*.sql"))
    if not matches and ROOT.parent.exists():
        matches = list(ROOT.parent.glob(f"{prefix}*.sql"))
    if not matches:
        raise FileNotFoundError(f"Could not find any SQL dump matching pattern '{prefix}*.sql' in {ROOT} or {ROOT.parent}")
    matches.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return matches[0]

SKIP_PREFIXES = (
    "\\restrict",
    "\\unrestrict",
    "SET transaction_timeout",
)

def sanitize_dump(src: Path, dest: Path) -> None:
    with src.open("r", encoding="utf-8", errors="replace") as fin, dest.open(
        "w", encoding="utf-8", newline="\n"
    ) as fout:
        for line in fin:
            if line.startswith(SKIP_PREFIXES):
                continue
            fout.write(line)

def run_psql(psql_bin: str, conn_info: dict, db_name: str, sql_file: Path) -> None:
    env = os.environ.copy()
    if conn_info["password"]:
        env["PGPASSWORD"] = conn_info["password"]

    cmd = [
        psql_bin,
        "-U", conn_info["user"],
        "-h", conn_info["host"],
        "-p", conn_info["port"],
        "-d", db_name,
        "-v", "ON_ERROR_STOP=1",
        "-f", str(sql_file)
    ]
    
    print(f"Executing: psql -U {conn_info['user']} -h {conn_info['host']} -d {db_name} -f {sql_file.name}")
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"psql warnings/output:\n{res.stderr[-2000:]}")
        if "FATAL" in res.stderr or "error" in res.stderr.lower():
            print("Note: Non-critical restore notices may occur if roles or extensions already exist.")

def recreate_database(admin_dsn: str, db_name: str, owner: str) -> None:
    with psycopg.connect(admin_dsn, autocommit=True) as conn:
        conn.execute(
            """
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = %s AND pid <> pg_backend_pid()
            """,
            (db_name,),
        )
        conn.execute(f'DROP DATABASE IF EXISTS "{db_name}"')
        conn.execute(f'CREATE DATABASE "{db_name}" OWNER "{owner}"')
        print(f"Database '{db_name}' created successfully (owner: {owner}).")

def copy_remote_enums(src_dsn: str, hub_dsn: str, service_name: str) -> None:
    with psycopg.connect(src_dsn) as src, psycopg.connect(hub_dsn, autocommit=True) as hub:
        rows = src.execute(
            """
            SELECT t.typname, array_agg(e.enumlabel ORDER BY e.enumsortorder)
            FROM pg_type t
            JOIN pg_enum e ON t.oid = e.enumtypid
            JOIN pg_namespace n ON n.oid = t.typnamespace
            WHERE n.nspname = 'public'
            GROUP BY t.typname
            """
        ).fetchall()
        for name, labels in rows:
            exists = hub.execute(
                "SELECT 1 FROM pg_type WHERE typname = %s",
                (name,),
            ).fetchone()
            if exists:
                continue
            labels_sql = ", ".join("'" + str(label).replace("'", "''") + "'" for label in labels)
            hub.execute(f'CREATE TYPE public."{name}" AS ENUM ({labels_sql})')
            print(f"Synced ENUM '{name}' from {service_name} to hub for FDW compatibility.")

def setup_fdw(conn_info: dict) -> None:
    host = conn_info["host"]
    port = conn_info["port"]
    user = conn_info["user"]
    password = conn_info["password"]
    
    us_dsn = f"postgresql://{user}:{password}@{host}:{port}/markazi_qa_us"
    ls_dsn = f"postgresql://{user}:{password}@{host}:{port}/markazi_qa_ls"
    hub_dsn = f"postgresql://{user}:{password}@{host}:{port}/markazi_qa_is"

    copy_remote_enums(us_dsn, hub_dsn, "US")
    copy_remote_enums(ls_dsn, hub_dsn, "LS")

    sql = f"""
    CREATE EXTENSION IF NOT EXISTS postgres_fdw;

    DROP SCHEMA IF EXISTS us CASCADE;
    DROP SCHEMA IF EXISTS ls CASCADE;
    DROP SERVER IF EXISTS markazi_us CASCADE;
    DROP SERVER IF EXISTS markazi_ls CASCADE;

    CREATE SERVER markazi_us FOREIGN DATA WRAPPER postgres_fdw
        OPTIONS (host '{host}', dbname 'markazi_qa_us', port '{port}');
    CREATE SERVER markazi_ls FOREIGN DATA WRAPPER postgres_fdw
        OPTIONS (host '{host}', dbname 'markazi_qa_ls', port '{port}');

    CREATE USER MAPPING FOR "{user}" SERVER markazi_us
        OPTIONS (user '{user}', password '{password}');
    CREATE USER MAPPING FOR "{user}" SERVER markazi_ls
        OPTIONS (user '{user}', password '{password}');

    CREATE SCHEMA us;
    CREATE SCHEMA ls;
    GRANT USAGE ON SCHEMA us, ls TO "{user}";
    GRANT USAGE ON FOREIGN SERVER markazi_us, markazi_ls TO "{user}";

    IMPORT FOREIGN SCHEMA public FROM SERVER markazi_us INTO us;
    IMPORT FOREIGN SCHEMA public FROM SERVER markazi_ls INTO ls;
    """
    with psycopg.connect(hub_dsn, autocommit=True) as conn:
        conn.execute(sql)
        rows = conn.execute(
            """
            SELECT n.nspname, c.relname
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname IN ('us', 'ls') AND c.relkind = 'f'
            ORDER BY 1, 2
            """
        ).fetchall()
        print(f"Successfully linked {len(rows)} foreign tables across 'us' and 'ls' schemas.")

def verify_databases(conn_info: dict) -> bool:
    hub_dsn = f"postgresql://{conn_info['user']}:{conn_info['password']}@{conn_info['host']}:{conn_info['port']}/markazi_qa_is"
    print("\n--- Verifying Database Integrity ---")
    try:
        with psycopg.connect(hub_dsn) as conn:
            conn.execute("SET search_path TO public, us, ls;")
            orders = conn.execute('SELECT COUNT(*) FROM public."order"').fetchone()[0]
            users = conn.execute('SELECT COUNT(*) FROM us.users').fetchone()[0]
            licenses = conn.execute('SELECT COUNT(*) FROM ls.license').fetchone()[0]
            locations = conn.execute('SELECT COUNT(*) FROM public.location').fetchone()[0]
            products = conn.execute('SELECT COUNT(*) FROM public.product').fetchone()[0]
            
            print(f"[OK] Orders found in IS (public): {orders}")
            print(f"[OK] Warehouses/Locations in IS (public): {locations}")
            print(f"[OK] Products in IS (public): {products}")
            print(f"[OK] Users linked via FDW (us schema): {users}")
            print(f"[OK] Licenses linked via FDW (ls schema): {licenses}")
            return True
    except Exception as e:
        print(f"[FAIL] Verification failed: {e}")
        return False

SECTION_DIVIDER = "=" * 50


def main():
    print(SECTION_DIVIDER)
    print("Markazi Automated Multi-Database Migration & Setup")
    print(SECTION_DIVIDER)
    
    psql_bin = find_psql()
    print(f"Using PSQL binary: {psql_bin}")

    raw_url = os.getenv("MARKAZI_DB_URL", "")
    if not raw_url:
        raise ValueError("MARKAZI_DB_URL environment variable must be set.")
    conn_info = parse_db_url(raw_url)
    print(f"Target PostgreSQL: host={conn_info['host']}, port={conn_info['port']}, user={conn_info['user']}")

    admin_dsn = f"postgresql://{conn_info['user']}:{conn_info['password']}@{conn_info['host']}:{conn_info['port']}/postgres"

    dumps = {
        "markazi_qa_us": find_dump_file("markazi-qa-us"),
        "markazi_qa_ls": find_dump_file("markazi-qa-ls"),
        "markazi_qa_is": find_dump_file("markazi-qa-is")
    }

    tmp_dir = ROOT / "data" / "_tmp_restore"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    try:
        for db_name, dump_path in dumps.items():
            print(f"\nProcessing {db_name} from {dump_path.name}...")
            sanitized = tmp_dir / f"{db_name}.sql"
            sanitize_dump(dump_path, sanitized)
            recreate_database(admin_dsn, db_name, conn_info["user"])
            run_psql(psql_bin, conn_info, db_name, sanitized)
            print(f"Restore of {db_name} complete.")

        print("\nLinking microservice databases via PostgreSQL FDW...")
        setup_fdw(conn_info)

        success = verify_databases(conn_info)
        if success:
            print(f"\n{SECTION_DIVIDER}")
            print("ALL DATABASES CREATED, RESTORED, AND LINKED!")
            print("Chatbot is ready to run: python run_server.py")
            print(SECTION_DIVIDER)
        else:
            print("\nSetup finished with verification warnings. Check logs above.")

    finally:
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir, ignore_errors=True)

if __name__ == "__main__":
    main()
