"""Shared enums/constants for the domain model (Blueprint §4-5).

Stored as plain strings in the DB (portable across SQLite/PostgreSQL — ADR-01) but
exposed as ``str, Enum`` so both Pydantic and business logic can validate against them.
"""
from __future__ import annotations

from enum import Enum


class ProjectType(str, Enum):
    NEW = "new"
    EXISTING = "existing"


class ProjectStatus(str, Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class TaskStatus(str, Enum):
    BACKLOG = "backlog"
    PLANNED = "planned"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    DEPLOYED = "deployed"
    ESCALATED = "escalated"  # revision failed MAX_REVISIONS times (Blueprint §5)


class AssigneeType(str, Enum):
    HUMAN = "human"
    AGENT = "agent"


class AgentRole(str, Enum):
    PM = "pm"
    DEV = "dev"
    SENIOR_ARCHITECT = "senior_architect"
    REVIEWER = "reviewer"


class Priority(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class AgentProvider(str, Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"


class AgentMode(str, Enum):
    SOLO = "solo"
    TEAM = "team"


class AgentStatus(str, Enum):
    IDLE = "idle"
    WORKING = "working"
    ERROR = "error"


class MessageType(str, Enum):
    HANDOFF = "handoff"
    QUESTION = "question"
    RESULT = "result"
    REVIEW_COMMENT = "review_comment"


class DeploymentTrigger(str, Enum):
    AUTO = "auto"
    MANUAL = "manual"


class DeploymentStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class ActorType(str, Enum):
    HUMAN = "human"
    AGENT = "agent"


# Escalation Rule — Max Revision = 2 (Blueprint §5 / DEVELOPMENT_PLAN §4).
MAX_REVISIONS = 2
