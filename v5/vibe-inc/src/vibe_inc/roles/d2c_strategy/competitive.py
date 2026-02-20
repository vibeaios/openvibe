"""CompetitiveIntel operator — tracks competitors and assesses threats."""
from openvibe_sdk import Operator, agent_node

from vibe_inc.tools.shared_memory import read_memory, write_memory
from vibe_inc.tools.web.search import web_fetch, web_search


class CompetitiveIntel(Operator):
    operator_id = "competitive_intel"

    @agent_node(
        tools=[web_search, web_fetch, read_memory, write_memory],
        output_key="scan_result",
    )
    def weekly_scan(self, state):
        """You are a competitive intelligence analyst for Vibe Inc.

        Perform a weekly competitive scan across Vibe's three product categories:
        1. Read the competitor registry from shared_memory
           (competitive/competitor_registry.yaml) to know who to track.
        2. For each competitor, search for recent news, product updates,
           pricing changes, and partnerships (last 7 days).
        3. Fetch key pages (pricing, features, blog) for any competitor
           showing significant activity.
        4. Update battlecards in shared_memory (competitive/battlecards/{competitor}.yaml)
           with new findings.
        5. Write a competitive digest to shared_memory
           (competitive/market-signals.yaml) with:
           - Major moves: product launches, pricing changes, funding
           - Minor signals: blog posts, feature updates, job postings
           - Risk assessment: low/medium/high per competitor

        Products to track against:
        - Vibe Bot: vs Owl Labs, Otter.ai, Jabra
        - Vibe Dot: vs Limitless, Plaud, Rewind
        - Vibe Board: vs Microsoft Surface Hub, Samsung Flip

        Know the enemy better than they know themselves.

        Return: competitive digest with categorized signals and updated battlecard summary."""
        period = state.get("period", "last_7d")
        return f"Run weekly competitive scan for period: {period}."

    @agent_node(
        tools=[web_search, web_fetch, read_memory],
        output_key="threat_result",
    )
    def threat_assess(self, state):
        """You are a competitive threat analyst for Vibe Inc.

        Given a specific competitive move (new product, price cut, partnership),
        assess its impact on Vibe:
        1. Read the competitor's battlecard from shared_memory
           (competitive/battlecards/{competitor}.yaml).
        2. Search for additional context on the move (press releases,
           analyst commentary, social sentiment).
        3. Fetch relevant pages for detailed analysis.
        4. Assess impact along three dimensions:
           - Revenue risk: could this move steal Vibe customers? (low/medium/high)
           - Positioning risk: does this undermine our messaging? (low/medium/high)
           - Timeline: how fast will this impact us? (immediate/quarterly/long-term)
        5. Recommend response options:
           - Do nothing (if low risk)
           - Update messaging (if positioning risk)
           - Accelerate feature/pricing response (if revenue risk)
           - Alert sales team (if immediate competitive deals at risk)

        This is analysis only — no writes to shared memory.
        Competitive alerts are autonomous notifications.

        Return: threat assessment with impact scores and recommended response."""
        competitor = state.get("competitor", "")
        move = state.get("move", "")
        return f"Assess threat from {competitor}: {move}."
