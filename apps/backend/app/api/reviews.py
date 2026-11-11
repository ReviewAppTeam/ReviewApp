from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_session
from app.models import Review
from app.services.review_import import CsvRowError, parse_reviews_csv, save_reviews

router = APIRouter(prefix="/reviews", tags=["reviews"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


class ReviewImportResult(BaseModel):
    received: int
    imported: int
    skipped_duplicates: int


class CsvImportErrorResponse(BaseModel):
    detail: str
    errors: list[CsvRowError]


class ReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    author: str | None
    rating: int
    text: str
    reviewed_at: datetime


class ReviewPage(BaseModel):
    items: list[ReviewRead]
    total: int
    page: int
    page_size: int


@router.post(
    "/import",
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": CsvImportErrorResponse},
        status.HTTP_413_CONTENT_TOO_LARGE: {"description": "File exceeds the size limit"},
    },
)
async def import_reviews(file: UploadFile, session: SessionDep) -> ReviewImportResult:
    """Imports reviews from a CSV with header `source,author,rating,text,date`."""
    rows = parse_reviews_csv(await _read_limited(file))
    imported = await save_reviews(session, rows)
    return ReviewImportResult(
        received=len(rows), imported=imported, skipped_duplicates=len(rows) - imported
    )


async def _read_limited(file: UploadFile) -> bytes:
    max_bytes = get_settings().csv_import_max_bytes
    content = await file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise HTTPException(
            status.HTTP_413_CONTENT_TOO_LARGE,
            f"File is larger than {max_bytes // 1024} KiB.",
        )
    return content


@router.get("")
async def list_reviews(
    session: SessionDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ReviewPage:
    """Returns reviews newest first."""
    total = (await session.execute(select(func.count()).select_from(Review))).scalar_one()
    reviews = await session.scalars(
        select(Review)
        .order_by(Review.reviewed_at.desc(), Review.id.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    return ReviewPage(
        items=[ReviewRead.model_validate(review) for review in reviews],
        total=total,
        page=page,
        page_size=page_size,
    )
