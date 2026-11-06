from dataclasses import dataclass

from pydantic import BaseModel

from src.llm.base import Message


@dataclass(frozen=True)
class RecordedCall:
    messages: list[Message]
    schema: type[BaseModel]


class FakeLLM:
    """LLM giả cho test: trả lần lượt các response viết sẵn, không gọi mạng."""

    def __init__(self, responses: list[dict | Exception]) -> None:
        self._responses = list(responses)
        self.calls: list[RecordedCall] = []

    def generate_json(self, messages: list[Message], schema: type[BaseModel]) -> dict:
        # Copy list: nếu caller append thêm message sau đó thì bản ghi cũ không bị đổi theo.
        self.calls.append(RecordedCall(messages=list(messages), schema=schema))

        if not self._responses:
            raise AssertionError("FakeLLM hết response kịch bản: code gọi LLM nhiều hơn test dự kiến.")

        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response
