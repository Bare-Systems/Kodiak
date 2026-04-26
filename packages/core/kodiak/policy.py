"""Headless execution policy for sensitive Kodiak actions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from kodiak.audit import log_action
from kodiak.errors import PolicyError


class ActionType(StrEnum):
    """Policy action classes."""

    READ = "read"
    PLAN = "plan"
    EXECUTE = "execute"


@dataclass(frozen=True)
class ExecutionPolicyDecision:
    """Policy decision attached to audit records."""

    action: str
    action_type: ActionType
    allowed: bool
    execution_intent: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize decision for audit/details payloads."""
        return {
            "action": self.action,
            "action_type": self.action_type.value,
            "allowed": self.allowed,
            "execution_intent": self.execution_intent,
            "reason": self.reason,
        }


def evaluate_execution_policy(
    action: str,
    *,
    action_type: ActionType,
    execution_intent: bool = False,
) -> ExecutionPolicyDecision:
    """Classify and decide whether an action is allowed."""
    if action_type is not ActionType.EXECUTE:
        return ExecutionPolicyDecision(
            action=action,
            action_type=action_type,
            allowed=True,
            execution_intent=execution_intent,
            reason=f"{action_type.value} action does not require execution intent",
        )

    if execution_intent:
        return ExecutionPolicyDecision(
            action=action,
            action_type=action_type,
            allowed=True,
            execution_intent=True,
            reason="explicit execution intent confirmed",
        )

    return ExecutionPolicyDecision(
        action=action,
        action_type=action_type,
        allowed=False,
        execution_intent=False,
        reason="explicit execution intent is required",
    )


def add_policy_details(
    details: dict[str, Any],
    decision: ExecutionPolicyDecision,
) -> dict[str, Any]:
    """Return details with policy decision metadata attached."""
    return {**details, "policy": decision.to_dict()}


def require_execution_intent(
    action: str,
    *,
    execution_intent: bool,
    log_dir: Path | None,
    details: dict[str, Any] | None = None,
) -> ExecutionPolicyDecision:
    """Require explicit intent for a sensitive execution action."""
    decision = evaluate_execution_policy(
        action,
        action_type=ActionType.EXECUTE,
        execution_intent=execution_intent,
    )
    if decision.allowed:
        return decision

    audit_details = add_policy_details(details or {}, decision)
    log_action(
        "execution_policy_blocked",
        audit_details,
        error=decision.reason,
        log_dir=log_dir,
    )
    raise PolicyError(
        message=f"{action} blocked by execution policy: {decision.reason}",
        details=audit_details,
        suggestion="Set confirm_execution=true for REST/MCP calls or use an explicit CLI command.",
    )
