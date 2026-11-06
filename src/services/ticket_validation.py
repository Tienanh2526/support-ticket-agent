from io import BytesIO

import pandas as pd

from src.schemas.validation import ValidationIssues, ValidationResult

# Theo docs/04_data_spec.md: chỉ 2 cột này bắt buộc, các cột khác là tuỳ chọn.
REQUIRED_COLUMNS = ["ticket_id", "body"]


class CSVReadError(ValueError):
    pass


class MissingColumnsError(ValueError):
    def __init__(self, missing_columns: list[str]) -> None:
        self.missing_columns = missing_columns
        super().__init__(f"Missing required columns: {missing_columns}")


def read_tickets_csv(content: bytes) -> pd.DataFrame:
    try:
        # utf-8-sig: bỏ ký tự BOM mà Excel hay chèn vào đầu file.
        # dtype=str: giữ nguyên ID như "001", không để pandas đổi thành số 1.
        return pd.read_csv(BytesIO(content), encoding="utf-8-sig", dtype=str)
    except Exception as exc:
        raise CSVReadError("Unable to read CSV file.") from exc


def _blank_rows(series: pd.Series) -> list[int]:
    """Trả về số dòng trong file CSV (dòng 1 là header) có giá trị rỗng."""
    is_blank = series.isna() | (series.astype(str).str.strip() == "")
    return [int(index) + 2 for index in series[is_blank].index]


def validate_tickets(df: pd.DataFrame, filename: str) -> ValidationResult:
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing_columns:
        raise MissingColumnsError(missing_columns)

    ticket_ids = df["ticket_id"].str.strip()
    duplicate_ids = sorted(
        ticket_ids[ticket_ids.duplicated() & ticket_ids.ne("")].dropna().unique()
    )

    issues = ValidationIssues(
        blank_ticket_id_rows=_blank_rows(df["ticket_id"]),
        blank_body_rows=_blank_rows(df["body"]),
        duplicate_ticket_ids=duplicate_ids,
    )
    has_issues = any(issues.model_dump().values())

    return ValidationResult(
        status="has_issues" if has_issues else "valid",
        filename=filename,
        total_tickets=len(df),
        columns=df.columns.tolist(),
        issues=issues,
    )
