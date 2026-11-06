from typing import Literal, Protocol, runtime_checkable

from pydantic import BaseModel


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class LLMError(RuntimeError):
    """Lỗi phía model: timeout, hết quota, provider trả lỗi."""


@runtime_checkable
class LLMClient(Protocol):
    def generate_json(self, messages: list[Message], schema: type[BaseModel]) -> dict:
        """Gửi messages, yêu cầu model trả JSON theo schema. Trả dict thô, chưa validate."""
        ...
