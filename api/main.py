from __future__ import annotations

from fastapi import FastAPI

from api.routers import channels, health, internal, requests, tracks

app = FastAPI(title="AI Music Station", version="0.1.0")

app.include_router(health.router)
app.include_router(channels.router)
app.include_router(requests.router)
app.include_router(tracks.router)
app.include_router(internal.router)
