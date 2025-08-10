import asyncio
import os
import sys
from pathlib import Path
import re
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv(dotenv_path=ROOT / ".env")
except Exception:
    pass

from app.core.logger import logger
from app.utils.database_utils import create_database_config, DatabaseType


async def main() -> None:
    cfg = create_database_config(DatabaseType.SUPABASE)
    # Mask password in logs
    masked = re.sub(r":[^:@]+@", ":****@", cfg.connection_string)
    logger.info(f"Testing DB connection to: {masked}")

    engine = create_async_engine(cfg.connection_string)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("DB connection successful (SELECT 1)")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
