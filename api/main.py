from __future__ import annotations

from fastapi import FastAPI

from api.routers import (
    analytics,
    channels,
    health,
    internal,
    podcasts,
    quality,
    reactions,
    requests,
    shares,
    tracks,
)

app = FastAPI(title="AI Music Station", version="0.1.0")

app.include_router(health.router)
app.include_router(channels.router)
app.include_router(requests.router)
app.include_router(tracks.router)
app.include_router(reactions.router)
app.include_router(podcasts.router)
app.include_router(shares.router)
app.include_router(analytics.router)
app.include_router(internal.router)
app.include_router(quality.router)
