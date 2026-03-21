from fastapi import FastAPI

app = FastAPI(title="AI Music Station", version="0.1.0")


@app.get("/api/health")
async def health() -> dict:
    return {"status": "healthy"}
