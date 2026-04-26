# Kodiak Operator Onboarding

This guide is the shortest safe path for a team using Kodiak as a headless trading and research product. Kodiak has no embedded trading dashboard by design. Operators use the CLI, agents use MCP, and integrations use authenticated REST.

## 1. Choose Your Runtime

Use **CLI-only** when one operator or one local agent runs Kodiak on a workstation:

```bash
git clone <repo-url>
cd Kodiak
pip install pipx
pipx install -e packages/cli/
kodiak status
```

Use **server mode** when remote agents, REST integrations, or scheduled server-side operations need a persistent endpoint:

```bash
git clone <repo-url>
cd Kodiak
pip install poetry
poetry install
poetry run kodiak-server
```

Server surfaces:
- `/` is a minimal headless landing page.
- `/health` is public and intended for monitoring.
- `/api/v1/*` is the authenticated REST API.
- `/api/docs` is the interactive REST documentation.
- `/api/v1/schema.json` is the REST OpenAPI export.
- `/mcp/` is the authenticated streamable-HTTP MCP endpoint.

## 2. Configure Paper Trading First

Start with Alpaca paper credentials. Do not configure production credentials until paper-mode workflows are understood and tested.

```bash
kodiak config set ALPACA_API_KEY your_paper_key
kodiak config set ALPACA_SECRET_KEY your_paper_secret
kodiak config list
```

For server REST/MCP access, set a bearer token before starting the server:

```bash
export KODIAK_API_TOKEN="$(openssl rand -hex 32)"
poetry run kodiak-server
```

Optional data environment:
- `HISTORICAL_DATA_DIR` points to CSV historical data for backtests, optimization, benchmark history, and portfolio analytics.
- `FUNDAMENTALS_DATA_DIR` points to file-backed fundamentals data.
- `KODIAK_DATABASE_URL` enables PostgreSQL-backed mutable state; otherwise Kodiak falls back to local YAML stores.

## 3. Connect Agents Through MCP

For local desktop agents, prefer stdio MCP:

```json
{
  "mcpServers": {
    "Kodiak": {
      "command": "/absolute/path/to/kodiak",
      "args": ["mcp"],
      "env": {
        "ALPACA_API_KEY": "your_paper_key",
        "ALPACA_SECRET_KEY": "your_paper_secret",
        "HISTORICAL_DATA_DIR": "/absolute/path/to/historical-csvs"
      }
    }
  }
}
```

For remote agents, start `kodiak-server` and connect to:

```text
http://localhost:8000/mcp/
```

Include:

```text
Authorization: Bearer <KODIAK_API_TOKEN>
```

After changing MCP tools or signatures, restart the agent client or reload the MCP server process so the new tool schema is visible.

## 4. Use Planning Tools Before Execution

Recommended operator/agent sequence:

1. Inspect runtime state: `get_status`.
2. Inspect portfolio state: `get_portfolio`, `get_positions`, `get_portfolio_analytics`.
3. Research and validate: `get_benchmark_history`, `get_fundamentals`, `run_backtest`, `run_optimization`.
4. Plan sizing: `calculate_position_size`.
5. Plan allocation changes: `get_rebalance_plan`.
6. Review proposed execution externally before placing or canceling orders.

Planning tools do not place orders. Sensitive execution tools require explicit intent.

## 5. Execute Safely

REST and MCP execution calls that place orders, cancel orders, start the engine, or stop the engine must pass `confirm_execution=true`. Without it, Kodiak returns `POLICY_BLOCKED` and writes an audit entry.

Blocked REST example:

```bash
curl -X POST http://localhost:8000/api/v1/engine/stop \
  -H "Authorization: Bearer $KODIAK_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"force": false}'
```

Confirmed REST example:

```bash
curl -X POST http://localhost:8000/api/v1/engine/stop \
  -H "Authorization: Bearer $KODIAK_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"force": false, "confirm_execution": true}'
```

Confirmed MCP example:

```json
{"tool": "stop_engine", "arguments": {"force": false, "confirm_execution": true}}
```

CLI execution commands pass explicit intent because a human directly invoked the command. Production CLI commands still prompt where applicable.

## 6. Validate A Deployment

Before publishing or deploying a change:

```bash
poetry run python scripts/export_contracts.py --check
poetry run python scripts/headless_smoke.py
poetry run ruff check .
poetry run mypy --config-file mypy-ci.ini packages/core/kodiak/app/orders.py packages/core/kodiak/app/portfolio.py packages/core/kodiak/app/research.py packages/core/kodiak/core/engine.py packages/core/kodiak/data/research.py packages/core/kodiak/mcp/tools.py packages/core/kodiak/schemas/research.py packages/core/kodiak/utils/logging.py packages/server/kodiak_server
poetry run pytest
```

The smoke harness is safe for routine release checks. It does not place orders or start the engine.

## 7. Audit And Troubleshoot

Operational checks:
- `kodiak status` confirms environment, broker config, and engine state.
- `kodiak strategy list` confirms loaded strategies.
- `poetry run python scripts/headless_smoke.py --json` gives machine-readable deployment smoke output.
- `GET /api/v1/schema.json` confirms REST contract availability.
- `poetry run python scripts/export_contracts.py --check` confirms checked-in REST/MCP contracts are current.

Common issues:
- If MCP tools are stale, restart the agent client or MCP server process.
- If CSV-backed tools cannot find data, set `HISTORICAL_DATA_DIR` in the same environment as the CLI, server, or MCP process.
- If REST or HTTP MCP returns `401`, check `KODIAK_API_TOKEN` and the `Authorization: Bearer ...` header.
- If an execution call returns `POLICY_BLOCKED`, add `confirm_execution=true` only after reviewing the requested action.
