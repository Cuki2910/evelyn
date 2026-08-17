from fastapi import FastAPI

app = FastAPI(title="Evelyn API", version="0.1.0")


@app.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
