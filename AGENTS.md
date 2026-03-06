# BareTrader - Codex Development Context

## Project Overview

BareTrader is a Python CLI tool for rule-based automated stock trading with paper and live trading support via Alpaca.

## Development Guidelines

1. Always refer to the [PLAN.md](./PLAN.md) for what to build and how. Keep it updated as you make changes.
2. Leverage abstractions and design code to be modular. 
3. Always keep the [README.md](./README.md), [CONTRIBUTING.md](./CONTRIBUTING.md), [PLAN.md](./PLAN.md), and [CHANGELOG.md](./CHANGELOG.md) updated as you code. Ensure you pause after making changes to consider how they affect documentation, and keep it updated. Documentation like this helps inform you about how things work, and keeping it updated ensures you are always informed about the state of the project.
4. Design the system with accessibility in mind for both human users, AI agents, and eventual integration into an MCP server
5. **Agentic development**: The MCP server (stdio) is the primary way an agent should exercise the app. Use the 32 MCP tools for all operations (status, strategies, backtests, etc.). Run CLI commands only when testing or verifying human-facing output (e.g. `baretrader status` or `baretrader --json status`). Training loop: call MCP tools → observe responses and test results → fix bugs in code/tests → re-run. See PLAN.md “Agentic development (goal)” for the full loop.

## Current Phase

**MCP Phase 4 - Docs + Contract Tests** ✅

**Recent Progress**:
- ✅ MCP Phase 3 complete: audit log, rate limits, timeouts for long-running tools
- ✅ MCP server (`trader/mcp/`) with 32 tools; `baretrader mcp serve` (stdio)
- ✅ CLI + MCP usage: `baretrader --help` and MCP tool list (per-feature command/tool mapping)
- ✅ Notifications (Discord + webhook), shared error hierarchy, Pydantic v2 schemas, app layer
- ✅ MCP contract tests (`tests/test_mcp_contract.py`) and CLI–MCP parity tests (`tests/test_cli_mcp_parity.py`)

## Architecture

The project uses a **dual-interface adapter pattern**:

```
trader/cli/    → Click commands (human-friendly, Rich tables)
trader/mcp/    → MCP server (agent-friendly, JSON via MCP SDK stdio)
baretrader/app/    → Shared application services (business logic)
baretrader/schemas/→ Pydantic v2 models (contracts)
trader/errors.py → Shared error hierarchy
```

Both CLI and MCP call the same `baretrader/app/` functions and use the same `baretrader/schemas/` contracts.

## Environment Variables

```env
# Paper trading
ALPACA_API_KEY=xxx
ALPACA_SECRET_KEY=xxx

# Production (separate keys)
ALPACA_PROD_API_KEY=xxx
ALPACA_PROD_SECRET_KEY=xxx
```

URLs are hardcoded per service. Use `--prod` flag for production.

## Agent Usage and Learning

When using BareTrader for exploration and strategy development:

- **MCP first**: Use MCP tools for all operations (get_status, list_strategies, run_backtest, etc.). The CLI is for humans; run CLI only when testing or verifying the human-facing experience (e.g. Rich tables or `baretrader --json <cmd>`).
- **[CONTEXTS.md](./CONTEXTS.md)** — Learning and discovery log. Document backtests, explorations, and learnings here.
- **[PORTFOLIO.md](./PORTFOLIO.md)** — Curated strategy portfolio. Add strategies only after extensive backtesting and validation.
- **Setup**: See README and CONTRIBUTING for MCP config; use the MCP tool list for workflows and tool reference.

**Key Distinction**: CONTEXTS.md = "What we're learning", PORTFOLIO.md = "What we're confident in"

### Available Prompts (Codex Desktop)

**Research & Discovery:**
- `.Codex/prompts/research-large-caps.md` - Autonomous research of major large-cap stocks (AAPL, GOOGL, MSFT, NVDA, etc.)
- `.Codex/prompts/research-sectors.md` - Sector-based equity discovery and strategy development
- `.Codex/prompts/explore-opportunities.md` - Autonomous discovery of new trading opportunities

**Strategy Development:**
- `.Codex/prompts/discover-strategies.md` - Guided strategy discovery for non-financial users
- `.Codex/prompts/explore-backtesting.md` - Comprehensive backtesting exploration
- `.Codex/prompts/curate-portfolio.md` - Portfolio curation workflow

**Portfolio Management:**
- `.Codex/prompts/rebalance-portfolio.md` - Interactive portfolio rebalancing with user approval for each trade
- `.Codex/prompts/monitor-portfolio.md` - Portfolio monitoring and allocation analysis
- `.Codex/prompts/review-daily-activity.md` - Review yesterday's trading activity, evaluate strategy performance, and propose adjustments with user approval
- `.Codex/prompts/create-strategies.md` - Create all strategies from PORTFOLIO.md
- `.Codex/prompts/portfolio-status.md` - Quick portfolio status overview

## Reference Files

- `PLAN.md` - Development roadmap (product phases + MCP + CLI)
- `CONTRIBUTING.md` - Setup, code style, and how to make changes
- `README.md` - User documentation
- `CHANGELOG.md` - Version history
- `.cursor/rules/baretrader.mdc` - Project rules and conventions (primary source)
