from enum import StrEnum

# Tăng version mỗi khi đổi nhãn, để kết quả eval cũ không bị so sánh nhầm.
TAXONOMY_VERSION = "0.1"


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
