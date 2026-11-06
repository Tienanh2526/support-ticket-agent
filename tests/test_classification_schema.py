import pytest
from pydantic import ValidationError

from src.schemas.classification import ClassificationOutput, ClassificationResult
from src.schemas.ticket import Category, TicketIn

VALID_OUTPUT = {
    "category": "refund_return",
    "priority": "medium",
    "sentiment": "neutral",
    "language": "en",
    "confidence": 0.9,
}


def test_valid_llm_output_is_parsed_into_enums() -> None:
    output = ClassificationOutput.model_validate(VALID_OUTPUT)

    assert output.category is Category.REFUND_RETURN


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("category", "refund"),  # nhãn không có trong taxonomy
        ("priority", "critical"),
        ("sentiment", "angry"),
        ("language", "fr"),
        ("confidence", 1.5),  # ngoài khoảng [0, 1]
        ("confidence", -0.1),
    ],
)
def test_invalid_llm_output_is_rejected(field: str, bad_value: object) -> None:
    with pytest.raises(ValidationError):
        ClassificationOutput.model_validate({**VALID_OUTPUT, field: bad_value})


def test_missing_field_is_rejected() -> None:
    incomplete = {k: v for k, v in VALID_OUTPUT.items() if k != "priority"}

    with pytest.raises(ValidationError):
        ClassificationOutput.model_validate(incomplete)


def test_result_adds_ticket_id_and_taxonomy_version() -> None:
    output = ClassificationOutput.model_validate(VALID_OUTPUT)
    result = ClassificationResult(ticket_id="tk_002", **output.model_dump())

    assert result.ticket_id == "tk_002"
    assert result.taxonomy_version == "0.1"


def test_ticket_in_only_requires_id_and_body() -> None:
    ticket = TicketIn(ticket_id="tk_008", body="Shop có hỗ trợ vào cuối tuần không ạ?")

    assert ticket.order_id is None
    assert ticket.language is None


def test_ticket_in_parses_created_at() -> None:
    ticket = TicketIn(ticket_id="t1", body="hi", created_at="2026-10-01T09:12:00")

    assert ticket.created_at.day == 1


@pytest.mark.parametrize("body", ["", "   "])
def test_ticket_in_rejects_blank_body(body: str) -> None:
    with pytest.raises(ValidationError):
        TicketIn(ticket_id="t1", body=body)
