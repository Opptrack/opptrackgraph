from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.core.logger import logger
from app.api.insights import router as insights_router
from app.api.config import router as config_router
from app.api.test import router as test_router
from app.utils.routes_middleware import RawRequestLoggerMiddleware


app = FastAPI(
    title="OppTrack API",
    description="API for OppTrack application",
    version="0.0.1",
    logger=logger,
)

app.add_middleware(
    RawRequestLoggerMiddleware,
    exclude_paths=["/health"],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()
app.include_router(router)
app.include_router(insights_router)
app.include_router(config_router)
app.include_router(test_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_config=logger,  # type: ignore
        log_level="info",
        access_log=True,
    )
