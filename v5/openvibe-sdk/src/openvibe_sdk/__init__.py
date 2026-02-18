"""OpenVibe SDK — 4-layer framework for human+agent collaboration."""

__version__ = "1.0.0"

from openvibe_sdk.operator import Operator, llm_node, agent_node
from openvibe_sdk.role import Role
from openvibe_sdk.runtime import OperatorRuntime, RoleRuntime

# V2 exports
from openvibe_sdk.memory.types import Fact, Episode, Insight, Classification
from openvibe_sdk.memory.access import ClearanceProfile
from openvibe_sdk.memory.workspace import WorkspaceMemory
from openvibe_sdk.memory.agent_memory import AgentMemory
from openvibe_sdk.memory.filesystem import MemoryFilesystem
from openvibe_sdk.models import AuthorityConfig

# V3 models
from openvibe_sdk.models import (
    Event, RoutingDecision, RoleMessage,
    WorkspaceConfig, WorkspacePolicy,
    RoleTemplate, RoleSpec,
    RoleLifecycle, RoleStatus,
    TrustProfile, Objective, KeyResult,
)

# V5 models
from openvibe_sdk.models import TenantContext, TemplateConfig, RoleInstance

# V5 registry
from openvibe_sdk.template_registry import TemplateRegistry

# V3 registry
from openvibe_sdk.registry import (
    Participant, RoleRegistry, RoleTransport,
    InMemoryRegistry, InMemoryTransport,
)

__all__ = [
    # V1
    "Operator",
    "llm_node",
    "agent_node",
    "Role",
    "OperatorRuntime",
    "RoleRuntime",
    # V2
    "Fact",
    "Episode",
    "Insight",
    "Classification",
    "ClearanceProfile",
    "WorkspaceMemory",
    "AgentMemory",
    "MemoryFilesystem",
    "AuthorityConfig",
    # V3 models
    "Event",
    "RoutingDecision",
    "RoleMessage",
    "WorkspaceConfig",
    "WorkspacePolicy",
    "RoleTemplate",
    "RoleSpec",
    "RoleLifecycle",
    "RoleStatus",
    "TrustProfile",
    "Objective",
    "KeyResult",
    # V3 registry
    "Participant",
    "RoleRegistry",
    "RoleTransport",
    "InMemoryRegistry",
    "InMemoryTransport",
    # V5 models
    "TenantContext",
    "TemplateConfig",
    "RoleInstance",
    # V5 registry
    "TemplateRegistry",
]
