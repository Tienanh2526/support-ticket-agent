from pydantic import BaseModel, Field

from src.schemas.ticket import TAXONOMY_VERSION, Category, Language, Priority, Sentiment


class ClassificationOutput(BaseModel):
    """Phần LLM phải điền. Không có ticket_id vì code đã biết sẵn."""

    category: Category
    priority: Priority
    sentiment: Sentiment
    language: Language
    confidence: float = Field(ge=0, le=1)


class ClassificationResult(ClassificationOutput):
    """Kết quả hệ thống trả ra: output của LLM + thông tin code tự gắn."""

    ticket_id: str
    taxonomy_version: str = TAXONOMY_VERSION
