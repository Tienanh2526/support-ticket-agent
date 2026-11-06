from fastapi import FastAPI

from src.api.router import api_router

app = FastAPI(
    title="Support Ticket Agent API",
    description="Triage customer support tickets and draft KB-grounded replies.",
    version="0.1.0",
)

app.include_router(api_router)


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "support-ticket-agent"}
