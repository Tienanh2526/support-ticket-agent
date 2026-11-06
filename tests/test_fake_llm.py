import pytest

from src.llm.base import LLMClient, LLMError, Message
from src.llm.fake import FakeLLM
from src.schemas.classification import ClassificationOutput

MESSAGES = [Message(role="user", content="Đơn ORD1001 đang ở đâu?")]


def test_fake_llm_satisfies_llm_client_protocol() -> None:
    assert isinstance(FakeLLM(responses=[]), LLMClient)


def test_returns_scripted_responses_in_order() -> None:
    fake = FakeLLM(responses=[{"n": 1}, {"n": 2}])

    assert fake.generate_json(MESSAGES, ClassificationOutput) == {"n": 1}
    assert fake.generate_json(MESSAGES, ClassificationOutput) == {"n": 2}


def test_records_messages_and_schema() -> None:
    fake = FakeLLM(responses=[{}])
    fake.generate_json(MESSAGES, ClassificationOutput)

    assert len(fake.calls) == 1
    assert fake.calls[0].messages[0].content == "Đơn ORD1001 đang ở đâu?"
    assert fake.calls[0].schema is ClassificationOutput


def test_recorded_messages_are_not_changed_by_caller() -> None:
    messages = list(MESSAGES)
    fake = FakeLLM(responses=[{}])
    fake.generate_json(messages, ClassificationOutput)

    messages.append(Message(role="user", content="thêm"))

    assert len(fake.calls[0].messages) == 1


def test_raises_scripted_exception() -> None:
    fake = FakeLLM(responses=[LLMError("timeout")])

    with pytest.raises(LLMError):
        fake.generate_json(MESSAGES, ClassificationOutput)


def test_fails_loudly_when_out_of_responses() -> None:
    fake = FakeLLM(responses=[])

    with pytest.raises(AssertionError):
        fake.generate_json(MESSAGES, ClassificationOutput)
