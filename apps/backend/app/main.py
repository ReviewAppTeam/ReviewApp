from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from app.api.reviews import CsvImportErrorResponse
from app.api.router import api_router
from app.config import get_settings
from app.services.review_import import CsvImportError


def operation_id(route: APIRoute) -> str:
    """Generated TS client names functions after this, e.g. `healthReadHealth`."""
    return f"{route.tags[0]}_{route.name}" if route.tags else route.name


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="ReviewApp API", version="0.1.0", generate_unique_id_function=operation_id)

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(api_router, prefix="/api/v1")
    app.add_exception_handler(CsvImportError, csv_import_error_handler)
    return app


async def csv_import_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, CsvImportError)
    body = CsvImportErrorResponse(detail=exc.message, errors=exc.errors)
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=body.model_dump())


app = create_app()
