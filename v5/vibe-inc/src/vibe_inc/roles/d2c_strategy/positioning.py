"""PositioningEngine operator — defines messaging frameworks, validates stories, refines ICP."""
from openvibe_sdk import Operator, agent_node

from vibe_inc.tools.ga4 import ga4_read
from vibe_inc.tools.shared_memory import read_memory, write_memory


class PositioningEngine(Operator):
    operator_id = "positioning_engine"

    @agent_node(
        tools=[read_memory, write_memory],
        output_key="framework_result",
    )
    def define_framework(self, state):
        """You are a product marketing strategist for Vibe Inc hardware products.

        Given product specs, market research, and ICP data, create a messaging framework:
        1. Read the current framework from shared_memory (messaging/{product}-framework.yaml).
           If none exists, start from scratch.
        2. Define the positioning hierarchy:
           - Primary message: one sentence, ruthlessly simple.
           - Supporting messages: 2-3 proof-point narratives.
           - Proof points: specific features/stats that validate the claim.
        3. For each competitor in the battlecard, define a differentiation line.
        4. Write the framework to shared_memory (messaging/{product}-framework.yaml)
           with status=draft.
        5. Include target_icp (primary + secondary) in the framework.

        Positioning is a bet — be opinionated, not hedging. One clear message per product.

        Return: the complete framework with primary/supporting/proof structure."""
        product = state.get("product", "bot")
        return f"Define messaging framework for {product}."

    @agent_node(
        tools=[ga4_read, read_memory, write_memory],
        output_key="validation_result",
    )
    def validate_story(self, state):
        """You are a story validation analyst for Vibe Inc.

        Given experiment data from D2C Growth, determine which narrative is winning:
        1. Read the messaging framework from shared_memory (messaging/{product}-framework.yaml).
        2. Read GA4 experiment data: compare variants on key metrics
           (CVR, revenue per visitor, bounce rate, time on page).
        3. Calculate statistical significance (need p < 0.05 for a winner call).
        4. If a winner emerges:
           - Recommend locking the positioning (status=locked).
           - Summarize why this narrative won (data + qualitative reasoning).
        5. If no winner yet:
           - Recommend continuing the test with specific duration estimate.
           - Identify which variants to drop (performing >30% below leader).
        6. Write updated validation status to shared_memory
           (performance/story-validation.yaml).

        Be data-driven but also interpret the qualitative signal. Numbers alone
        don't pick the best story — the story that resonates is the one that
        changes behavior.

        Return: winner analysis with confidence score, or keep-testing recommendation."""
        product = state.get("product", "bot")
        experiment_id = state.get("experiment_id", "")
        return f"Validate story for {product}, experiment {experiment_id}."

    @agent_node(
        tools=[read_memory, write_memory],
        output_key="icp_result",
    )
    def refine_icp(self, state):
        """You are an ICP (Ideal Customer Profile) analyst for Vibe Inc.

        Refine the target customer definition based on purchase data, surveys, and CRM signals:
        1. Read current ICP from shared_memory (audiences/icp-definitions.yaml).
        2. Analyze the input data:
           - Purchase patterns: who buys, average order value, repeat rate.
           - Survey signals: what pain points resonate, what features matter.
           - CRM enrichment: company size, industry, role of buyer.
        3. Update the ICP with:
           - Primary persona: the single best customer archetype.
           - Secondary persona: the next-best segment.
           - Anti-persona: who is NOT the customer (saves ad spend).
        4. Write updated ICP to shared_memory (audiences/icp-definitions.yaml).

        ICP clarity > broad reach. A tight ICP that converts at 5% beats a broad
        one that converts at 0.5%.

        Note: ICP redefinition requires human approval before committing changes.

        Return: updated ICP definitions with reasoning and data evidence."""
        product = state.get("product", "bot")
        return f"Refine ICP for {product}."
