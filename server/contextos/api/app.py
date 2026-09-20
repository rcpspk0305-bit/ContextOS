from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextos.api.routes import router as api_router
from contextos.api.websocket import router as ws_router

def create_app() -> FastAPI:
    app = FastAPI(
        title="ContextOS AI Operating Layer",
        description="Local-first AI supervisor, context broker, and Model Context Protocol daemon.",
        version="0.1.0",
    )

    # Enable local CORS for frontend control center
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)
    app.include_router(ws_router)

    return app

app = create_app()
