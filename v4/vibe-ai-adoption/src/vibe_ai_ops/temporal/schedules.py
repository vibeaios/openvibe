from __future__ import annotations

from vibe_ai_ops.shared.models import AgentConfig


def parse_cron_to_temporal(cron_expr: str) -> dict:
    """Parse 5-field cron to Temporal ScheduleSpec fields."""
    parts = cron_expr.split()
    if len(parts) != 5:
        raise ValueError(f"Invalid cron: {cron_expr}")

    minute, hour, day, month, dow = parts

    def parse_field(val: str) -> list[int] | None:
        if val == "*":
            return None
        return [int(v) for v in val.split(",")]

    result = {}
    if minute != "*":
        result["minute"] = parse_field(minute)
    if hour != "*":
        result["hour"] = parse_field(hour)
    if day != "*":
        result["day_of_month"] = parse_field(day)
    if month != "*":
        result["month"] = parse_field(month)
    if dow != "*":
        result["day_of_week"] = parse_field(dow)
    return result


def build_schedule_specs(configs: list[AgentConfig]) -> list[dict]:
    """Build Temporal schedule specs for all cron-triggered agents."""
    specs = []
    for config in configs:
        if config.trigger.type.value == "cron" and config.trigger.schedule:
            cron_spec = parse_cron_to_temporal(config.trigger.schedule)
            specs.append({
                "agent_id": config.id,
                "name": config.name,
                "cron_spec": cron_spec,
                "cron_expression": config.trigger.schedule,
            })
    return specs
