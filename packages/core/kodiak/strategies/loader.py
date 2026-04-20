"""Strategy loading and persistence.

Routes to the PostgreSQL store when KODIAK_DATABASE_URL is configured,
otherwise falls back to YAML (config/strategies.yaml) for local dev and CI.
"""

from datetime import datetime
from pathlib import Path

import yaml

from kodiak.strategies.models import Strategy


def _use_postgres() -> bool:
    """True when KODIAK_DATABASE_URL is set — use the Postgres store."""
    import os
    return bool(os.getenv("KODIAK_DATABASE_URL"))


def get_strategies_file(config_dir: Path | None = None) -> Path:
    """Get path to strategies file."""
    if config_dir is None:
        from kodiak.utils.paths import get_config_dir
        config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "strategies.yaml"


def load_strategies(config_dir: Path | None = None) -> list[Strategy]:
    """Load all strategies (Postgres if configured, else YAML)."""
    if _use_postgres():
        from kodiak.db.pg_strategy_store import load_strategies as _pg
        return _pg()

    strategies_file = get_strategies_file(config_dir)
    if not strategies_file.exists():
        return []
    with open(strategies_file) as f:
        data = yaml.safe_load(f)
    if not data or "strategies" not in data:
        return []
    return [Strategy.from_dict(s) for s in data["strategies"]]


def save_strategies(strategies: list[Strategy], config_dir: Path | None = None) -> None:
    """Batch save strategies (Postgres if configured, else YAML)."""
    if _use_postgres():
        from kodiak.db.pg_strategy_store import save_strategies as _pg
        return _pg(strategies)

    strategies_file = get_strategies_file(config_dir)
    data = {"strategies": [s.to_dict() for s in strategies]}
    with open(strategies_file, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def save_strategy(strategy: Strategy, config_dir: Path | None = None) -> None:
    """Add or update a single strategy (Postgres if configured, else YAML)."""
    if _use_postgres():
        from kodiak.db.pg_strategy_store import save_strategy as _pg
        return _pg(strategy)

    strategies = load_strategies(config_dir)
    existing_idx = None
    for i, s in enumerate(strategies):
        if s.id == strategy.id:
            existing_idx = i
            break
    strategy.updated_at = datetime.now()
    if existing_idx is not None:
        strategies[existing_idx] = strategy
    else:
        strategies.append(strategy)
    save_strategies(strategies, config_dir)


def delete_strategy(strategy_id: str, config_dir: Path | None = None) -> bool:
    """Delete a strategy by ID. Returns True if deleted."""
    if _use_postgres():
        from kodiak.db.pg_strategy_store import delete_strategy as _pg
        return _pg(strategy_id)

    strategies = load_strategies(config_dir)
    original_count = len(strategies)
    strategies = [s for s in strategies if s.id != strategy_id]
    if len(strategies) == original_count:
        return False
    save_strategies(strategies, config_dir)
    return True


def get_strategy(strategy_id: str, config_dir: Path | None = None) -> Strategy | None:
    """Get a strategy by ID, or None if not found."""
    if _use_postgres():
        from kodiak.db.pg_strategy_store import get_strategy as _pg
        return _pg(strategy_id)

    strategies = load_strategies(config_dir)
    for s in strategies:
        if s.id == strategy_id:
            return s
    return None


def enable_strategy(strategy_id: str, enabled: bool = True, config_dir: Path | None = None) -> bool:
    """Enable or disable a strategy. Returns True if found and updated."""
    if _use_postgres():
        from kodiak.db.pg_strategy_store import enable_strategy as _pg
        return _pg(strategy_id, enabled)

    strategy = get_strategy(strategy_id, config_dir)
    if strategy is None:
        return False
    strategy.enabled = enabled
    save_strategy(strategy, config_dir)
    return True


def get_active_strategies(config_dir: Path | None = None) -> list[Strategy]:
    """Get all active (non-terminal, enabled, schedule-ready) strategies."""
    if _use_postgres():
        from kodiak.db.pg_strategy_store import get_active_strategies as _pg
        return _pg()

    strategies = load_strategies(config_dir)
    now = datetime.now()
    active = []
    for s in strategies:
        if not s.enabled:
            continue
        if s.schedule_enabled and s.schedule_at and s.schedule_at > now:
            continue
        if not s.is_active():
            continue
        active.append(s)
    return active
