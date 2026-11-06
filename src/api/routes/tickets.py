from fastapi import APIRouter, File, HTTPException, UploadFile, status

from src.schemas.validation import ValidationResult
from src.services.ticket_validation import (
    CSVReadError,
    MissingColumnsError,
    read_tickets_csv,
    validate_tickets,
)

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.post("/validate", response_model=ValidationResult)
async def validate_tickets_csv(file: UploadFile = File(...)) -> ValidationResult:
    # Route chỉ lo HTTP: kiểm tra file, gọi service, đổi exception thành status code.
    filename = file.filename or ""
    if not filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Please upload a .csv file.",
        )

    content = await file.read()

    try:
        df = read_tickets_csv(content)
        return validate_tickets(df, filename)
    except CSVReadError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except MissingColumnsError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Missing required columns.",
                "missing_columns": exc.missing_columns,
            },
        )
