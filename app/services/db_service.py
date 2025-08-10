from supabase._async.client import AsyncClient as Client, create_client

from app.config.config import app_settings


async def create_supabase() -> Client:
    return await create_client(app_settings.SUPABASE_URL, app_settings.SUPABASE_KEY)
