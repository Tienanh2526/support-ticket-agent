from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Tăng version mỗi khi đổi nhãn, để kết quả eval cũ không bị so sánh nhầm.
TAXONOMY_VERSION = "0.1"

# Dùng chung cho ticket đầu vào và kết quả phân loại.
Language = Literal["vi", "en"]


class Category(StrEnum):
    ORDER_STATUS = "order_status"
    SHIPPING_DELIVERY = "shipping_delivery"
    REFUND_RETURN = "refund_return"
    PAYMENT_BILLING = "payment_billing"
    PRODUCT_ISSUE = "product_issue"
    ACCOUNT_ACCESS = "account_access"
    PROMOTION_VOUCHER = "promotion_voucher"
    OTHER = "other"


class Priority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Sentiment(StrEnum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    MIXED = "mixed"
    UNCLEAR = "unclear"


class TriageAction(StrEnum):
    # Agent chỉ soạn nháp, không bao giờ tự gửi cho khách.
    DRAFT_REPLY = "draft_reply"
    ESCALATE = "escalate"


class TicketIn(BaseModel):
    # Bỏ khoảng trắng đầu/cuối trước khi kiểm tra min_length,
    # nên body "   " bị coi là rỗng và bị từ chối.
    model_config = ConfigDict(str_strip_whitespace=True)

    ticket_id: str = Field(min_length=1)
    body: str = Field(min_length=1)
    subject: str | None = None
    created_at: datetime | None = None
    channel: str | None = None
    # None = để bước phân loại tự nhận diện ngôn ngữ.
    language: Language | None = None
    order_id: str | None = None
    customer_id: str | None = None
