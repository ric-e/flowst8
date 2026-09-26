import os
import asyncpg
from dotenv import load_dotenv

# Load variables from backend/app/.env
load_dotenv()

DB_USER = os.getenv("POSTGRES_USER", "flowst8")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "flowst8")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "flowst8")

# Build the connection URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# We'll store a global connection pool so we don't open/close connections constantly
db_pool = None

async def init_db():
    """
    Creates the connection pool, standard tables, and TimescaleDB hypertables.
    Call this once when your backend server starts up.
    """
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(DATABASE_URL)

    async with db_pool.acquire() as conn:
        # 1. Create the standard table
        # Notice we use TIMESTAMPTZ (timezone-aware timestamp), which is a Timescale requirement
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS keystroke_metrics (
                time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                session_id UUID NOT NULL,
                keystrokes_per_min DOUBLE PRECISION NOT NULL,
                backspace_ratio DOUBLE PRECISION NOT NULL
            );
        ''')
        
        # 2. Convert to TimescaleDB Hypertable
        # This automatically partitions data by time for massive query performance
        await conn.execute('''
            SELECT create_hypertable('keystroke_metrics', 'time', if_not_exists => TRUE);
        ''')
        print("TimescaleDB extension verified and tables initialized.")

async def insert_keystroke_metrics(session_id: str, keystrokes_per_min: float, backspace_ratio: float):
    """
    Inserts a single WS payload aggregate into the database.
    """
    if db_pool is None:
        raise RuntimeError("Database pool not initialized. Call init_db() first.")

    async with db_pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO keystroke_metrics (session_id, keystrokes_per_min, backspace_ratio)
            VALUES ($1, $2, $3)
        ''', session_id, keystrokes_per_min, backspace_ratio)

async def close_db():
    """
    Gracefully closes the database pool. Call this when your server shuts down.
    """
    global db_pool
    if db_pool:
        await db_pool.close()