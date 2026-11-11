import csv
import hashlib
import io
from collections.abc import Sequence
from datetime import UTC, datetime
from itertools import batched

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Review

EXPECTED_COLUMNS = ("source", "author", "rating", "text", "date")
MAX_REPORTED_ERRORS = 50
INSERT_BATCH_SIZE = 1000


class CsvRowError(BaseModel):
    line: int
    column: str | None
    message: str


class CsvImportError(Exception):
    def __init__(self, message: str, errors: Sequence[CsvRowError] = ()) -> None:
        super().__init__(message)
        self.message = message
        self.errors = list(errors)


class ReviewRow(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    source: str = Field(min_length=1, max_length=50)
    author: str | None = Field(default=None, max_length=255)
    rating: int = Field(ge=1, le=5)
    text: str = Field(min_length=1)
    date: datetime

    @field_validator("author", mode="before")
    @classmethod
    def blank_author_is_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("date")
    @classmethod
    def assume_utc_when_naive(cls, value: datetime) -> datetime:
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value

    def content_hash(self) -> str:
        parts = (
            self.source,
            self.author or "",
            str(self.rating),
            self.text,
            self.date.astimezone(UTC).isoformat(),
        )
        return hashlib.sha256("\x1f".join(parts).encode()).hexdigest()


def parse_reviews_csv(content: bytes) -> list[ReviewRow]:
    try:
        decoded = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise CsvImportError("File must be UTF-8 encoded CSV.") from exc

    reader = csv.reader(io.StringIO(decoded, newline=""))
    header = next(reader, None)
    if header is None:
        raise CsvImportError("File is empty.")
    columns = _validate_header(header)

    rows: list[ReviewRow] = []
    errors: list[CsvRowError] = []
    for values in reader:
        if not any(value.strip() for value in values):
            continue
        if len(values) != len(columns):
            errors.append(
                CsvRowError(
                    line=reader.line_num,
                    column=None,
                    message=f"Expected {len(columns)} values, got {len(values)}.",
                )
            )
            continue
        try:
            rows.append(ReviewRow.model_validate(dict(zip(columns, values, strict=True))))
        except ValidationError as exc:
            errors.extend(_row_errors(reader.line_num, exc))

    if errors:
        raise CsvImportError(
            f"File has {len(errors)} invalid value(s); nothing was imported.",
            errors[:MAX_REPORTED_ERRORS],
        )
    return rows


def _validate_header(header: list[str]) -> list[str]:
    columns = [column.strip().lower() for column in header]
    missing = [column for column in EXPECTED_COLUMNS if column not in columns]
    unexpected = [column for column in columns if column not in EXPECTED_COLUMNS]
    duplicated = sorted({column for column in columns if columns.count(column) > 1})

    problems: list[str] = []
    if missing:
        problems.append(f"missing: {', '.join(missing)}")
    if unexpected:
        problems.append(f"unexpected: {', '.join(unexpected)}")
    if duplicated:
        problems.append(f"duplicated: {', '.join(duplicated)}")
    if problems:
        raise CsvImportError(
            f"Invalid CSV columns ({'; '.join(problems)}). "
            f"Expected header: {','.join(EXPECTED_COLUMNS)}."
        )
    return columns


def _row_errors(line: int, exc: ValidationError) -> list[CsvRowError]:
    return [
        CsvRowError(
            line=line,
            column=str(error["loc"][0]) if error["loc"] else None,
            message=error["msg"],
        )
        for error in exc.errors()
    ]


async def save_reviews(session: AsyncSession, rows: Sequence[ReviewRow]) -> int:
    """Inserts rows that are not stored yet and returns how many were inserted."""
    inserted = 0
    for batch in batched(rows, INSERT_BATCH_SIZE, strict=False):
        statement = (
            insert(Review)
            .values([_to_values(row) for row in batch])
            .on_conflict_do_nothing(index_elements=[Review.content_hash])
            .returning(Review.id)
        )
        result = await session.execute(statement)
        inserted += len(result.scalars().all())
    await session.commit()
    return inserted


def _to_values(row: ReviewRow) -> dict[str, object]:
    return {
        "source": row.source,
        "author": row.author,
        "rating": row.rating,
        "text": row.text,
        "reviewed_at": row.date,
        "content_hash": row.content_hash(),
    }
