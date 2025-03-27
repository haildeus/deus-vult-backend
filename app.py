from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.api_router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup events

    yield

    # Shutdown events


app = FastAPI(lifespan=lifespan)

# That's for the cors plugin
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "ETag",
        "Cache-Control",
        "If-None-Match",
        "Vary",
        "CDN-Cache-Control",
    ],
)

app.include_router(api_router)
