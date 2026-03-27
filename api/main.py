from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routers import (
    analytics,
    channels,
    generate,
    health,
    internal,
    playlists,
    podcasts,
    quality,
    reactions,
    requests,
    shares,
    tracks,
)
from api.services.generation_worker import start_worker, stop_worker


@asynccontextmanager
async def lifespan(app: FastAPI):
    await start_worker()
    yield
    await stop_worker()


app = FastAPI(title="AI Music Station", version="0.1.0", lifespan=lifespan)

app.include_router(health.router)
app.include_router(channels.router)
app.include_router(requests.router)
app.include_router(generate.router)
app.include_router(tracks.router)
app.include_router(reactions.router)
app.include_router(playlists.router)
app.include_router(podcasts.router)
app.include_router(shares.router)
app.include_router(analytics.router)
app.include_router(internal.router)
app.include_router(quality.router)
