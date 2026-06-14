from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.db.base import Base
from app.db.session import get_engine


def create_app() -> FastAPI:
    app = FastAPI(title="Software Cup A3 Learning Backend")

    # CORS – allow frontend dev server and production builds
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:5173",
            "http://localhost:5173",
            "http://127.0.0.1:8000",
            "http://localhost:8000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api/v1")

    # Ensure database tables exist on startup
    Base.metadata.create_all(get_engine())

    return app


app = create_app()
