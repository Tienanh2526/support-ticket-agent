from pathlib import Path

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)

SAMPLE_CSV = Path("data/raw/sample_tickets_synthetic.csv")


def post_csv(content: bytes, filename: str = "tickets.csv"):
    return client.post(
        "/api/v1/tickets/validate",
        files={"file": (filename, content, "text/csv")},
    )


def test_rejects_non_csv() -> None:
    response = post_csv(b"not a csv", "tickets.txt")
    assert response.status_code == 415


def test_accepts_sample_file() -> None:
    response = post_csv(SAMPLE_CSV.read_bytes(), SAMPLE_CSV.name)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "valid"
    assert body["total_tickets"] > 0
    assert "ticket_id" in body["columns"]


def test_rejects_missing_required_columns() -> None:
    response = post_csv(b"subject,channel\nHello,email\n")

    assert response.status_code == 400
    assert response.json()["detail"]["missing_columns"] == ["ticket_id", "body"]


def test_optional_columns_not_required() -> None:
    response = post_csv(b"ticket_id,body\nt1,Where is my order?\n")

    assert response.status_code == 200
    assert response.json()["status"] == "valid"


def test_flags_blank_values_and_duplicate_ids() -> None:
    csv = (
        b"ticket_id,body\n"
        b"t1,Where is my order?\n"
        b"t1,I want a refund\n"
        b",Cannot log in\n"
        b"t3,   \n"
    )
    response = post_csv(csv)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "has_issues"
    assert body["issues"] == {
        "blank_ticket_id_rows": [4],
        "blank_body_rows": [5],
        "duplicate_ticket_ids": ["t1"],
    }
