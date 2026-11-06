from typing import Literal

from pydantic import BaseModel


class ValidationIssues(BaseModel):
    blank_ticket_id_rows: list[int]
    blank_body_rows: list[int]
    duplicate_ticket_ids: list[str]


class ValidationResult(BaseModel):
    status: Literal["valid", "has_issues"]
    filename: str
    total_tickets: int
    columns: list[str]
    issues: ValidationIssues
