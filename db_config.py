# db_config.py
import logging
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional
import re

from databases import Database
from fastapi import FastAPI
from dotenv import load_dotenv
import os
import urllib.parse


load_dotenv()

# ------------------------------------------------------------
# Logging setup
# ------------------------------------------------------------
logger = logging.getLogger("db")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)

logger.setLevel(logging.CRITICAL)
# Or you can globally disable all loggers if needed:
# logging.disable(logging.CRITICAL)

class DatabaseManager:
    def __init__(self, database_url: str):
        self.database_url = database_url

        # SQLite doesn't support pooling, databases will handle it transparently
        if database_url.startswith("sqlite"):
            self.database = Database(database_url)
            self.pooling = False
        else:
            self.database = Database(
                database_url,
                min_size=5,
                max_size=20,
                timeout=30.0,
            )
            self.pooling = True

    # ----------------------------
    # FastAPI lifecycle events
    # ----------------------------
    def register_events(self, app: FastAPI):
        @app.on_event("startup")
        async def startup():
            await self.connect()

        @app.on_event("shutdown")
        async def shutdown():
            await self.disconnect()

    async def connect(self):
        if not self.database.is_connected:
            await self.database.connect()
            logger.info(
                f"Connected to DB ({'with pooling' if self.pooling else 'no pooling'})"
            )
            # If DB_SCHEMA is set, attempt to ensure the schema exists and set the search_path
            schema = os.getenv("DB_SCHEMA")
            if schema:
                try:
                    # Create schema if it doesn't exist (no-op if already present)
                    await self.database.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
                    # Set the search_path so unqualified table names resolve to the schema
                    await self.database.execute(f'SET search_path TO "{schema}", public')
                    logger.info(f'Set search_path to "{schema}"')
                except Exception as _err:
                    # Don't fail the entire app if setting schema fails; just log a warning
                    logger.warning(f'Unable to set search_path to "{schema}": {_err}')

    async def disconnect(self):
        if self.database.is_connected:
            await self.database.disconnect()
            logger.info("Disconnected from DB")

    # ----------------------------
    # CRUD helpers with logging
    # ----------------------------
    async def _log_query(self, query: str, values: Optional[Dict[str, Any]], start_time: float):
        elapsed = (time.monotonic() - start_time) * 1000
        formatted_query = query.strip().replace("\n", " ")
        logger.info(f"[{elapsed:.2f} ms] SQL: {formatted_query} | Params: {values}")

    async def read(self, conn: Database, query: str, values: Optional[Dict[str, Any]] = None):
        start = time.monotonic()
        result = await conn.fetch_all(query=query, values=values)
        await self._log_query(query, values, start)
        return [dict(r) for r in result]

    async def insert(self, conn: Database, query: str, values: Optional[Dict[str, Any]] = None):
        start = time.monotonic()
        result = await conn.execute(query=query, values=values)
        await self._log_query(query, values, start)
        return result

    async def update(self, conn: Database, query: str, values: Optional[Dict[str, Any]] = None):
        start = time.monotonic()
        result = await conn.execute(query=query, values=values)
        await self._log_query(query, values, start)
        return result

    async def delete(self, conn: Database, query: str, values: Optional[Dict[str, Any]] = None):
        start = time.monotonic()
        result = await conn.execute(query=query, values=values)
        await self._log_query(query, values, start)
        return result

    # ----------------------------
    # Context manager for DI
    # ----------------------------
    @asynccontextmanager
    async def connection(self):
        """
        Provide a per-request transaction and the Database handle.
        All operations within the context use the same underlying connection.
        """
        db_id = id(self.database)
        logger.info(f"→ Begin transaction on DB #{db_id}")
        async with self.database.transaction():
            try:
                # Ensure per-transaction search_path is set so unqualified names
                # resolve to the configured schema even for pooled connections.
                schema = os.getenv("DB_SCHEMA")
                if schema:
                    # Basic validation to avoid SQL injection via schema name
                    if re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', schema):
                        try:
                            # Use SET LOCAL so this applies only to the current transaction
                            await self.database.execute(f'SET LOCAL search_path TO "{schema}", public')
                            logger.info(f"Applied SET LOCAL search_path TO '{schema}' for transaction #{db_id}")
                        except Exception as _e:
                            logger.warning(f"Failed to SET LOCAL search_path to '{schema}': {_e}")
                    else:
                        logger.warning(f"DB_SCHEMA '{schema}' contains invalid characters and will be ignored")

                yield self.database
            finally:
                logger.info(f"← End transaction on DB #{db_id}")


# ------------------------------------------------------------
# Instance setup
# ------------------------------------------------------------
username = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
host = os.getenv("DB_HOST")
db = os.getenv("DB_NAME")
port = os.getenv("DB_PORT")

# DATABASE_URL = "sqlite+aiosqlite:///database.db"
base_url = f"postgresql+asyncpg://{username}:{password}@{host}:{port}/{db}"


db = DatabaseManager(base_url)


# ------------------------------------------------------------
# Dependency for FastAPI
# ------------------------------------------------------------
async def get_connection():
    """Dependency injection provider for FastAPI routes."""
    async with db.connection() as conn:
        yield conn


