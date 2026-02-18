from openvibe_runtime.audit import AuditLog, AuditEntry, compute_cost


def test_audit_entry_fields():
    entry = AuditEntry(
        role_id="cro", operator_id="revenue_ops",
        node_name="qualify_lead", action="llm_call",
        tokens_in=150, tokens_out=300,
        latency_ms=420, cost_usd=0.002,
    )
    assert entry.cost_usd == 0.002
    assert entry.tokens_in == 150


def test_audit_log_records_entry():
    log = AuditLog()
    log.record(AuditEntry(role_id="cro", operator_id="rev",
                          node_name="qualify", action="llm_call",
                          tokens_in=100, tokens_out=200,
                          latency_ms=300, cost_usd=0.001))
    assert len(log.entries) == 1


def test_audit_log_filter_by_role():
    log = AuditLog()
    log.record(AuditEntry(role_id="cro", operator_id="r", node_name="n",
                          action="a", tokens_in=1, tokens_out=1,
                          latency_ms=1, cost_usd=0.0))
    log.record(AuditEntry(role_id="cmo", operator_id="r", node_name="n",
                          action="a", tokens_in=1, tokens_out=1,
                          latency_ms=1, cost_usd=0.0))
    cro_entries = log.filter(role_id="cro")
    assert len(cro_entries) == 1


def test_audit_log_total_cost():
    log = AuditLog()
    for cost in [0.001, 0.002, 0.003]:
        log.record(AuditEntry(role_id="cro", operator_id="r", node_name="n",
                              action="a", tokens_in=1, tokens_out=1,
                              latency_ms=1, cost_usd=cost))
    assert abs(log.total_cost() - 0.006) < 0.0001


def test_audit_log_cost_by_role():
    log = AuditLog()
    log.record(AuditEntry(role_id="cro", operator_id="r", node_name="n",
                          action="a", tokens_in=1, tokens_out=1,
                          latency_ms=1, cost_usd=0.005))
    log.record(AuditEntry(role_id="cmo", operator_id="r", node_name="n",
                          action="a", tokens_in=1, tokens_out=1,
                          latency_ms=1, cost_usd=0.003))
    breakdown = log.cost_by_role()
    assert abs(breakdown["cro"] - 0.005) < 0.0001
    assert abs(breakdown["cmo"] - 0.003) < 0.0001


def test_compute_cost():
    cost = compute_cost(tokens_in=1_000_000, tokens_out=1_000_000)
    assert abs(cost - 18.0) < 0.001  # $3 in + $15 out
