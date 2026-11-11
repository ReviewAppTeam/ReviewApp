from pathlib import Path

import httpx2 as httpx
import pytest
from fastapi.testclient import TestClient

from app.config import get_settings

SAMPLE_CSV = Path(__file__).resolve().parent.parent / "samples" / "reviews.csv"
SAMPLE_ROWS = 25
HEADER = "source,author,rating,text,date\n"


def upload(client: TestClient, content: bytes) -> httpx.Response:
    return client.post(
        "/api/v1/reviews/import", files={"file": ("reviews.csv", content, "text/csv")}
    )


def total_reviews(client: TestClient) -> int:
    total: int = client.get("/api/v1/reviews").json()["total"]
    return total


def test_sample_csv_is_imported_and_listed(db_client: TestClient) -> None:
    response = upload(db_client, SAMPLE_CSV.read_bytes())

    assert response.status_code == 200
    assert response.json() == {
        "received": SAMPLE_ROWS,
        "imported": SAMPLE_ROWS,
        "skipped_duplicates": 0,
    }
    assert total_reviews(db_client) == SAMPLE_ROWS


def test_reimporting_same_file_creates_no_duplicates(db_client: TestClient) -> None:
    upload(db_client, SAMPLE_CSV.read_bytes())

    response = upload(db_client, SAMPLE_CSV.read_bytes())

    assert response.status_code == 200
    assert response.json() == {
        "received": SAMPLE_ROWS,
        "imported": 0,
        "skipped_duplicates": SAMPLE_ROWS,
    }
    assert total_reviews(db_client) == SAMPLE_ROWS


def test_duplicate_rows_within_file_are_stored_once(db_client: TestClient) -> None:
    row = "google_play,Olena,5,Great app,2026-10-01T10:00:00Z\n"
    # Naive date is treated as UTC, so this row is the same review as the first one.
    same_review = "google_play, Olena ,5,Great app,2026-10-01 10:00\n"

    response = upload(db_client, (HEADER + row + row + same_review).encode())

    assert response.json() == {"received": 3, "imported": 1, "skipped_duplicates": 2}


def test_values_are_normalized(db_client: TestClient) -> None:
    csv = HEADER + " app_store ,  ,4,  Nice  ,2026-10-01T12:00:00+03:00\n"

    upload(db_client, csv.encode("utf-8-sig"))

    [review] = db_client.get("/api/v1/reviews").json()["items"]
    assert review["source"] == "app_store"
    assert review["author"] is None
    assert review["text"] == "Nice"
    assert review["reviewed_at"] == "2026-10-01T09:00:00Z"


def test_columns_are_matched_case_insensitively_in_any_order(db_client: TestClient) -> None:
    csv = "Date,Text,Rating,Author,Source\n2026-10-01,Good,5,Ann,trustpilot\n"

    response = upload(db_client, csv.encode())

    assert response.status_code == 200
    assert response.json()["imported"] == 1


def test_wrong_columns_return_clear_error(db_client: TestClient) -> None:
    csv = "source,author,stars,review,date\ngoogle_play,Ann,5,Good,2026-10-01\n"

    response = upload(db_client, csv.encode())

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Invalid CSV columns (missing: rating, text; unexpected: stars, review). "
        "Expected header: source,author,rating,text,date.",
        "errors": [],
    }
    assert total_reviews(db_client) == 0


def test_invalid_rows_reject_whole_file(db_client: TestClient) -> None:
    csv = (
        HEADER
        + "google_play,Ann,5,Good,2026-10-01\n"
        + "google_play,Bob,7,Too high,2026-10-02\n"
        + "app_store,Eve,3,,not-a-date\n"
        + "app_store,Eve,3\n"
    )

    response = upload(db_client, csv.encode())

    assert response.status_code == 400
    body = response.json()
    assert body["detail"] == "File has 4 invalid value(s); nothing was imported."
    assert [(error["line"], error["column"]) for error in body["errors"]] == [
        (3, "rating"),
        (4, "text"),
        (4, "date"),
        (5, None),
    ]
    assert total_reviews(db_client) == 0


@pytest.mark.parametrize(
    ("content", "detail"),
    [
        (b"", "File is empty."),
        (
            (HEADER + "google_play,Ann,5,Відгук,2026-10-01\n").encode("cp1251"),
            "File must be UTF-8 encoded CSV.",
        ),
    ],
)
def test_unreadable_files_are_rejected(db_client: TestClient, content: bytes, detail: str) -> None:
    response = upload(db_client, content)

    assert response.status_code == 400
    assert response.json()["detail"] == detail


def test_file_over_size_limit_is_rejected(
    db_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(get_settings(), "csv_import_max_bytes", 1024)

    response = upload(db_client, (HEADER + "x" * 2048).encode())

    assert response.status_code == 413
