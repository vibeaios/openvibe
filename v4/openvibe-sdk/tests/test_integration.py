"""Integration test -- full example using all 4 layers."""

from openvibe_sdk import (
    Operator, Role, RoleRuntime, agent_node, llm_node,
)
from openvibe_sdk.llm import LLMResponse, ToolCall


class IntegrationLLM:
    def __init__(self):
        self.calls = []

    def call(self, *, system, messages, **kwargs):
        self.calls.append({"system": system, "messages": messages, **kwargs})

        if "research analyst" in system.lower():
            research_calls = [c for c in self.calls if "research analyst" in c["system"].lower()]
            if len(research_calls) == 1:
                return LLMResponse(
                    content="",
                    tool_calls=[
                        ToolCall(id="tc_1", name="fake_search", input={"query": "company info"})
                    ],
                    stop_reason="tool_use",
                )
            return LLMResponse(content="Acme is a B2B SaaS company.")

        if "qualifier" in system.lower():
            return LLMResponse(content='{"score": 85, "tier": "high"}')

        return LLMResponse(content="default response")


def fake_search(query: str) -> str:
    """Search for company information."""
    return f"Found: {query} - Acme Corp, B2B SaaS, 200 employees"


class CompanyIntel(Operator):
    operator_id = "company_intel"

    @agent_node(tools=[fake_search], output_key="research")
    def research(self, state):
        """You are a research analyst. Research the company thoroughly."""
        return f"Research: {state['company']}"

    @llm_node(model="sonnet", output_key="qualification")
    def qualify(self, state):
        """You are a lead qualifier. Score the prospect."""
        return f"Qualify based on: {state.get('research', 'unknown')}"


class CRO(Role):
    role_id = "cro"
    soul = "You are the CRO. Aggressive but data-driven."
    operators = [CompanyIntel]


def test_full_stack():
    llm = IntegrationLLM()

    runtime = RoleRuntime(roles=[CRO], llm=llm)

    role = runtime.get_role("cro")
    operator = role.get_operator("company_intel")

    state = {"company": "Acme Corp"}
    result = operator.research(state)
    assert "research" in result
    assert isinstance(result["research"], str)

    result["research"] = "Acme is a B2B SaaS company."
    result = operator.qualify(result)
    assert "qualification" in result

    for call in llm.calls:
        assert "CRO" in call["system"]


def test_public_api_exports():
    from openvibe_sdk import (
        Operator, llm_node, agent_node, Role, OperatorRuntime, RoleRuntime,
    )
    assert Operator is not None
    assert llm_node is not None
    assert agent_node is not None
    assert Role is not None
    assert OperatorRuntime is not None
    assert RoleRuntime is not None
