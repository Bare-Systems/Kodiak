"""Tests for headless execution policy."""

from pathlib import Path

import pytest
from kodiak.errors import PolicyError
from kodiak.policy import ActionType, evaluate_execution_policy, require_execution_intent


def test_read_and_plan_actions_do_not_require_execution_intent() -> None:
    read_decision = evaluate_execution_policy("get_positions", action_type=ActionType.READ)
    plan_decision = evaluate_execution_policy("get_rebalance_plan", action_type=ActionType.PLAN)

    assert read_decision.allowed is True
    assert plan_decision.allowed is True
    assert read_decision.action_type == ActionType.READ
    assert plan_decision.action_type == ActionType.PLAN


def test_execute_action_requires_explicit_intent() -> None:
    decision = evaluate_execution_policy("place_order", action_type=ActionType.EXECUTE)

    assert decision.allowed is False
    assert decision.execution_intent is False
    assert decision.reason == "explicit execution intent is required"


def test_require_execution_intent_logs_blocked_decision(tmp_path: Path) -> None:
    with pytest.raises(PolicyError) as exc_info:
        require_execution_intent(
            "cancel_order",
            execution_intent=False,
            log_dir=tmp_path,
            details={"order_id": "order-1"},
        )

    assert exc_info.value.code == "POLICY_BLOCKED"
    record = __import__("json").loads((tmp_path / "audit.log").read_text().strip())
    assert record["action"] == "execution_policy_blocked"
    assert record["details"]["order_id"] == "order-1"
    assert record["details"]["policy"]["action"] == "cancel_order"
    assert record["details"]["policy"]["action_type"] == "execute"
    assert record["details"]["policy"]["allowed"] is False


def test_require_execution_intent_returns_allowed_decision(tmp_path: Path) -> None:
    decision = require_execution_intent(
        "place_order",
        execution_intent=True,
        log_dir=tmp_path,
        details={"symbol": "AAPL"},
    )

    assert decision.allowed is True
    assert not (tmp_path / "audit.log").exists()
