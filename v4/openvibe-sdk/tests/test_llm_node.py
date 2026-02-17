import json

from openvibe_sdk.llm import LLMResponse
from openvibe_sdk.operator import Operator, llm_node


class FakeLLM:
    """Fake LLM provider for testing."""

    def __init__(self, response_content="test output"):
        self.response_content = response_content
        self.last_call = None

    def call(self, *, system, messages, **kwargs):
        self.last_call = {
            "system": system,
            "messages": messages,
            **kwargs,
        }
        return LLMResponse(
            content=self.response_content,
            tokens_in=10,
            tokens_out=20,
            model=kwargs.get("model", "haiku"),
        )


class SampleOperator(Operator):
    operator_id = "test_op"

    @llm_node(model="sonnet", temperature=0.3, output_key="result")
    def analyze(self, state):
        """You are a test analyst."""
        return f"Analyze: {state['input']}"


def test_operator_has_id():
    op = SampleOperator()
    assert op.operator_id == "test_op"


def test_operator_accepts_llm():
    llm = FakeLLM()
    op = SampleOperator(llm=llm)
    assert op.llm is llm


def test_llm_node_uses_docstring_as_system_prompt():
    llm = FakeLLM()
    op = SampleOperator(llm=llm)
    op.analyze({"input": "hello"})
    assert llm.last_call["system"] == "You are a test analyst."


def test_llm_node_uses_return_as_user_message():
    llm = FakeLLM()
    op = SampleOperator(llm=llm)
    op.analyze({"input": "hello"})
    messages = llm.last_call["messages"]
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Analyze: hello"


def test_llm_node_passes_model_and_temperature():
    llm = FakeLLM()
    op = SampleOperator(llm=llm)
    op.analyze({"input": "x"})
    assert llm.last_call["model"] == "sonnet"
    assert llm.last_call["temperature"] == 0.3


def test_llm_node_writes_output_key():
    llm = FakeLLM(response_content="analysis result")
    op = SampleOperator(llm=llm)
    state = {"input": "hello"}
    result = op.analyze(state)
    assert result["result"] == "analysis result"


def test_llm_node_auto_parses_json():
    json_response = json.dumps({"score": 85, "label": "high"})
    llm = FakeLLM(response_content=json_response)
    op = SampleOperator(llm=llm)
    state = {"input": "x"}
    result = op.analyze(state)
    assert isinstance(result["result"], dict)
    assert result["result"]["score"] == 85


def test_llm_node_returns_raw_string_on_non_json():
    llm = FakeLLM(response_content="just plain text")
    op = SampleOperator(llm=llm)
    state = {"input": "x"}
    result = op.analyze(state)
    assert result["result"] == "just plain text"


def test_llm_node_returns_state():
    llm = FakeLLM()
    op = SampleOperator(llm=llm)
    state = {"input": "x", "existing": "preserved"}
    result = op.analyze(state)
    assert result["existing"] == "preserved"
    assert "result" in result


def test_llm_node_no_output_key():
    class NoKeyOp(Operator):
        @llm_node(model="haiku")
        def process(self, state):
            """You are a processor."""
            return "process this"

    llm = FakeLLM(response_content="done")
    op = NoKeyOp(llm=llm)
    state = {"input": "x"}
    result = op.process(state)
    assert result is state  # state returned but no key written


def test_llm_node_marks_method():
    op = SampleOperator()
    assert hasattr(op.analyze, "_is_llm_node")
    assert op.analyze._is_llm_node is True
