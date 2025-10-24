# db_config.py
import logging
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

from databases import Database
from fastapi import FastAPI

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
        return result

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
                yield self.database
            finally:
                logger.info(f"← End transaction on DB #{db_id}")


# ------------------------------------------------------------
# Instance setup
# ------------------------------------------------------------
DATABASE_URL = "sqlite+aiosqlite:///database.db"
# DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/dbname"
# DATABASE_URL = "mysql+asyncmy://user:pass@localhost/dbname"

db = DatabaseManager(DATABASE_URL)


# ------------------------------------------------------------
# Dependency for FastAPI
# ------------------------------------------------------------
async def get_connection():
    """Dependency injection provider for FastAPI routes."""
    async with db.connection() as conn:
        yield conn