from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from Src.api.routes import router
from Src.cache.cache_manager import RankingCache
from Src.cache.dataset_tracker import DatasetTracker
from Src.common.errors import RankingError
from Src.common.utils import error_response
from Src.config import load_settings



def create_app() -> FastAPI:
    app = FastAPI(title="E-Commerce Ranking API", version="0.1.0")
    settings = load_settings()

    app.state.settings = settings
    app.state.cache = (
        RankingCache(
            max_cache_size_mb=settings.max_cache_size_mb,
            ttl_seconds=settings.cache_ttl_seconds,
        )
        if settings.cache_enabled
        else None
    )
    app.state.dataset_tracker = DatasetTracker(settings.dataset_path)
    app.state.dataset_tracker.reset()
    app.state.dataset = None

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    @app.exception_handler(RankingError)
    async def handle_ranking_error(_: Request, exc: RankingError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(exc.error_code, exc.message),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content=error_response("missing_required_param", str(exc.errors())),
        )

    return app


app = create_app()
