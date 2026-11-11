from fastapi.testclient import TestClient

CSV = (
    "source,author,rating,text,date\n"
    "google_play,Old,3,Oldest review,2026-01-01T00:00:00Z\n"
    "app_store,New,5,Newest review,2026-03-01T00:00:00Z\n"
    "trustpilot,Mid,4,Middle review,2026-02-01T00:00:00Z\n"
)


def import_reviews(client: TestClient) -> None:
    response = client.post(
        "/api/v1/reviews/import", files={"file": ("reviews.csv", CSV.encode(), "text/csv")}
    )
    assert response.status_code == 200


def test_empty_list(db_client: TestClient) -> None:
    response = db_client.get("/api/v1/reviews")

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "page": 1, "page_size": 20}


def test_reviews_are_listed_newest_first(db_client: TestClient) -> None:
    import_reviews(db_client)

    items = db_client.get("/api/v1/reviews").json()["items"]

    assert [item["author"] for item in items] == ["New", "Mid", "Old"]
    assert items[0] == {
        "id": items[0]["id"],
        "source": "app_store",
        "author": "New",
        "rating": 5,
        "text": "Newest review",
        "reviewed_at": "2026-03-01T00:00:00Z",
    }


def test_reviews_are_paginated(db_client: TestClient) -> None:
    import_reviews(db_client)

    first = db_client.get("/api/v1/reviews", params={"page": 1, "page_size": 2}).json()
    second = db_client.get("/api/v1/reviews", params={"page": 2, "page_size": 2}).json()
    beyond = db_client.get("/api/v1/reviews", params={"page": 3, "page_size": 2}).json()

    assert [item["author"] for item in first["items"]] == ["New", "Mid"]
    assert [item["author"] for item in second["items"]] == ["Old"]
    assert beyond["items"] == []
    assert first["total"] == second["total"] == 3
    assert (second["page"], second["page_size"]) == (2, 2)


def test_invalid_pagination_params_are_rejected(db_client: TestClient) -> None:
    assert db_client.get("/api/v1/reviews", params={"page": 0}).status_code == 422
    assert db_client.get("/api/v1/reviews", params={"page_size": 101}).status_code == 422
