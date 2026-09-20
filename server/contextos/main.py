import uvicorn
from contextos.config import settings

def main():
    print(f"[ContextOS Daemon] Starting local AI operating layer on {settings.HOST}:{settings.PORT}")
    uvicorn.run(
        "contextos.api.app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
        log_level="info",
    )

if __name__ == "__main__":
    main()
