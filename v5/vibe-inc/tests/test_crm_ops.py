from openvibe_sdk.llm import LLMResponse


def _text_response(content="done"):
    return LLMResponse(content=content, stop_reason="end_turn")


class FakeAgentLLM:
    """Fake LLM that returns pre-configured responses in sequence."""
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def call(self, *, system, messages, **kwargs):
        self.calls.append({"system": system, "messages": messages, **kwargs})
        return self.responses.pop(0)


# --- workflow_trigger ---

def test_workflow_trigger_is_agent_node():
    from vibe_inc.roles.d2c_growth.crm_ops import CRMOps
    assert hasattr(CRMOps.workflow_trigger, "_is_agent_node")
    assert CRMOps.workflow_trigger._is_agent_node is True
    assert "hubspot_workflow_enroll" in CRMOps.workflow_trigger._node_config["tools"]


def test_workflow_trigger_output_key():
    from vibe_inc.roles.d2c_growth.crm_ops import CRMOps

    llm = FakeAgentLLM([_text_response("Enrolled buyer@acme.com in b2b_onboarding")])
    op = CRMOps(llm=llm)
    result = op.workflow_trigger({"contact_email": "buyer@acme.com", "signal": "b2b_enriched"})

    assert "enrollment_result" in result


# --- deal_manage ---

def test_deal_manage_is_agent_node():
    from vibe_inc.roles.d2c_growth.crm_ops import CRMOps
    assert hasattr(CRMOps.deal_manage, "_is_agent_node")
    assert CRMOps.deal_manage._is_agent_node is True
    assert "hubspot_deal_create" in CRMOps.deal_manage._node_config["tools"]


def test_deal_manage_mentions_approval():
    from vibe_inc.roles.d2c_growth.crm_ops import CRMOps
    # The system prompt (docstring) should mention human approval for deal creation
    doc = CRMOps.deal_manage.__doc__
    assert "approval" in doc.lower() or "human" in doc.lower()
