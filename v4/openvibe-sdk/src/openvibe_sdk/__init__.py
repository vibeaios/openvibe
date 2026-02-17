"""OpenVibe SDK — 4-layer framework for human+agent collaboration."""

__version__ = "0.2.0"

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
]
