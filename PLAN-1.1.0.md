# PLAN 1.1.0 — Issues and Requirements from Financial Manager MCP Test Run

**Source**: TEST-PLAN.md Run 1 (2026-02-13)  
**Scope**: Large or structural issues (not fixed in Run 1). Small fixes already committed: `Strategy.from_dict` hyphen normalizer, indicator error suggestion.

## Completion Snapshot (2026-03-11)

Phase 1.1 is now complete in code and docs. All four issues below were implemented and validated in the app/server test suite; remaining MCP-client failures in prior runs were due to stale processes not yet restarted.

- ✅ Issue 1 complete: strategy loading accepts `pullback-trailing` and `pullback_trailing`
- ✅ Issue 2 complete: optimization normalizes short parameter names to canonical `_pct` keys
- ✅ Issue 3 complete: CSV backtest docs and error guidance updated
- ✅ Issue 4 complete: tool visibility troubleshooting documented; tool listing script added

Follow-up operational note: restart any long-lived MCP client/server process to pick up latest package code.

---

## Issue 1: Strategy Tools Fail When Config Contains `pullback_trailing` 🔴

**Status**: ✅ **COMPLETE**

**Priority**: ⭐⭐⭐⭐⭐ (Blocks all strategy operations)

### Why This Matters
- **For Humans**: Cannot list, create, or manage strategies if config contains `pullback_trailing` type
- **For AI Agents**: Strategy lifecycle operations (`list_strategies`, `create_strategy`, `get_strategy`) fail with `StrategyType` validation error
- **For MCP Server**: Breaks core workflow for financial manager persona

### Observed Behavior
- `list_strategies()` raises: `'pullback_trailing' is not a valid StrategyType`
- `create_strategy()` fails with same error (when loading existing strategies)
- `get_strategy(strategy_id)` fails (even for non-existent IDs, because it loads all strategies first)
- Error occurs when `strategies.yaml` contains `strategy_type: pullback_trailing` or `pullback-trailing`

### Root Cause Analysis
1. **YAML format mismatch**: Config may store `strategy_type: pullback-trailing` (hyphen) but enum expects `pullback_trailing` (underscore)
2. **Enum loading**: `Strategy.from_dict()` calls `StrategyType(data["strategy_type"])` which fails if value doesn't match enum exactly
3. **MCP process environment**: MCP server may run with different config dir or installed package version than development environment

### Implementation Details

#### Files Updated
- ✅ `packages/core/kodiak/strategies/models.py` — normalization `"pullback-trailing"` → `"pullback_trailing"` in `Strategy.from_dict()`
- ✅ `tests/core/test_app_services.py` — regression coverage for loading hyphen-formatted strategy type

#### Code Changes Required

**Already Fixed** (`trader/strategies/models.py`):
```python
@classmethod
def from_dict(cls, data: dict) -> "Strategy":
    """Create strategy from dictionary."""
    raw = data["strategy_type"]
    # Normalize CLI-style hyphen to enum value (e.g. pullback-trailing -> pullback_trailing)
    if raw == "pullback-trailing":
        raw = "pullback_trailing"
    return cls(
        ...
        strategy_type=StrategyType(raw),
        ...
    )
```

**Follow-up Actions** (if error persists after MCP restart):
1. Verify enum `StrategyType.PULLBACK_TRAILING = "pullback_trailing"` exists in running code
2. Add normalization for `pullback_trailing` → `pullback_trailing` (idempotent)
3. Audit all strategy load paths (`load_strategies`, `get_strategy`, `create_strategy` validation)
4. Add test: `test_strategy_load_with_hyphen_format()` in `tests/test_strategies.py`

### Acceptance Criteria
- ✅ `Strategy.from_dict()` normalizes `"pullback-trailing"` → `"pullback_trailing"`
- ✅ `list_strategies()` succeeds when config contains hyphen or underscore form
- ✅ `create_strategy()` succeeds regardless of existing config format
- ✅ `get_strategy()` succeeds (including non-existent IDs returning proper NotFoundError)
- ✅ Documentation updated in release notes and test plan artifacts

### Testing Strategy
```python
# tests/test_strategies_loader.py
def test_load_strategy_with_hyphen_format():
    """Test that strategies.yaml with pullback-trailing loads correctly."""
    data = {"strategy_type": "pullback-trailing", ...}
    strategy = Strategy.from_dict(data)
    assert strategy.strategy_type == StrategyType.PULLBACK_TRAILING

def test_list_strategies_with_mixed_formats():
    """Test list_strategies when config has both hyphen and underscore forms."""
    # Create test config with both formats
    # Verify list_strategies() succeeds
```

---

## Issue 2: `run_optimization` Parameter Key Mismatch 🔴

**Status**: ✅ **COMPLETE**

**Priority**: ⭐⭐⭐⭐ (Blocks optimization workflow)

### Why This Matters
- **For Humans**: Optimization fails with confusing error about missing params
- **For AI Agents**: Cannot optimize bracket strategies via MCP without knowing internal param key format
- **For MCP Server**: Tool contract doesn't match actual validation requirements

### Observed Behavior
- `run_optimization(strategy_type="bracket", ..., params={"take_profit": [0.02, 0.05], "stop_loss": [0.01, 0.02]})` returns: `Missing required parameters: take_profit_pct, stop_loss_pct`
- MCP tool description doesn't specify required param key format
- Backtest accepts `take_profit` / `stop_loss` but optimization requires `take_profit_pct` / `stop_loss_pct`

### Root Cause Analysis
1. **Inconsistent naming**: Backtest layer accepts `take_profit` / `stop_loss`; optimization layer expects `take_profit_pct` / `stop_loss_pct`
2. **Validation mismatch**: `_validate_optimization_params()` checks for `_pct` keys directly
3. **Missing normalization**: No mapping layer converts CLI/MCP-friendly names to internal format

### Implementation Details

#### Files Updated
- ✅ `packages/core/kodiak/app/optimization.py` — key normalization (`take_profit`/`stop_loss` → `_pct`) before validation
- ✅ `tests/core/test_optimization_params.py` — normalization and run-path regression tests
- ✅ `README.md` — optimization examples use canonical parameter keys

#### Code Changes Required

**Option A: Normalize in app layer** (`trader/app/optimization.py`):
```python
def _normalize_param_keys(params: dict[str, Any]) -> dict[str, Any]:
    """Normalize CLI/MCP-friendly param names to internal format."""
    normalized = params.copy()
    if "take_profit" in normalized and "take_profit_pct" not in normalized:
        normalized["take_profit_pct"] = normalized.pop("take_profit")
    if "stop_loss" in normalized and "stop_loss_pct" not in normalized:
        normalized["stop_loss_pct"] = normalized.pop("stop_loss")
    return normalized

def run_optimization(config: Config, request: OptimizeRequest) -> OptimizeResponse:
    """Run strategy parameter optimization."""
    # Normalize param keys before validation
    request.params = _normalize_param_keys(request.params)
    _validate_optimization_params(request.strategy_type, request.params)
    ...
```

**Option B: Document only** (if normalization is undesirable):
- Update MCP tool docstring: `params` must use `take_profit_pct` and `stop_loss_pct` for bracket strategy
- Update README with example: `{"take_profit_pct": [0.02, 0.05], "stop_loss_pct": [0.01, 0.02]}`

### Acceptance Criteria
- ✅ `run_optimization(..., params={"take_profit": [...], "stop_loss": [...]})` succeeds
- ✅ README includes optimization parameter examples
- ✅ `test_optimization_with_short_param_names()` verifies normalization

### Testing Strategy
```python
# tests/test_optimization.py
def test_optimization_normalizes_param_keys():
    """Test that take_profit/stop_loss normalize to _pct form."""
    request = OptimizeRequest(
        strategy_type="bracket",
        params={"take_profit": [0.02], "stop_loss": [0.01]},
        ...
    )
    # Verify normalization happens before validation
    result = run_optimization(config, request)
    assert result is not None
```

---

## Issue 3: Backtest/Optimization CSV Data Path Documentation 🔴

**Status**: ✅ **COMPLETE**

**Priority**: ⭐⭐⭐ (User experience)

### Why This Matters
- **For Humans**: Unclear how to set up CSV data for backtesting
- **For AI Agents**: Cannot run CSV backtests without knowing expected directory structure
- **For MCP Server**: Error message helpful but setup not documented

### Observed Behavior
- `run_backtest(..., data_source="csv")` returns: `DATA_NOT_FOUND: Data directory not found: /Users/joecaruso/data/historical`
- Error message suggests path but doesn't explain how to configure it
- No documentation on CSV file format or directory structure

### Root Cause Analysis
1. **Environment variable**: `HISTORICAL_DATA_DIR` not set; defaults to `~/data/historical` or config dir
2. **Missing docs**: README doesn't explain CSV setup for backtesting
3. **No examples**: No sample CSV files or directory structure documented

### Implementation Details

#### Files Updated
- ✅ `README.md` — expanded "Backtesting" section with CSV setup, format, and troubleshooting
- ✅ `packages/core/kodiak/app/backtests.py` — improved data-not-found message with setup guidance
- ✅ `packages/core/kodiak/data/providers/csv_provider.py` — improved missing-file/dir messages with README pointer

#### Documentation to Add

**README.md section**:
```markdown
## Backtesting with CSV Data

Set `HISTORICAL_DATA_DIR` environment variable or use default `~/.baretrader/data/historical/`.

CSV format: `{SYMBOL}.csv` with columns: `date, open, high, low, close, volume`
Example: `AAPL.csv`, `MSFT.csv`

For testing, create minimal CSV:
```bash
mkdir -p ~/.baretrader/data/historical
# Add sample CSV files
```
```

**Error message improvement** (`trader/backtest/data.py`):
```python
raise FileNotFoundError(
    f"CSV file not found: {csv_path}. "
    f"Set HISTORICAL_DATA_DIR or create {default_dir}/{{SYMBOL}}.csv. "
    f"See README.md 'Backtesting with CSV Data' section."
)
```

### Acceptance Criteria
- ✅ README documents CSV setup and format
- ✅ Error messages include setup guidance and README pointer
- ✅ Behavior covered by existing backtest/data-path tests and exercised in financial-manager run logs

### Testing Strategy
```python
# tests/test_backtest_data.py
def test_csv_error_message_helpful():
    """Test that CSV not found error includes setup instructions."""
    with pytest.raises(FileNotFoundError) as exc:
        load_price_data("AAPL", data_source="csv")
    assert "HISTORICAL_DATA_DIR" in str(exc.value)
    assert "README" in str(exc.value)
```

---

## Issue 4: MCP Tools Not Visible in Client 🔴

**Status**: ✅ **COMPLETE**

**Priority**: ⭐⭐ (Testing convenience)

### Why This Matters
- **For Testing**: Some tools (`list_scheduled_strategies`, `get_top_movers`) not visible in MCP client (e.g. Cursor)
- **For AI Agents**: Cannot discover all available tools via standard MCP tool list
- **For MCP Server**: All 32+ tools implemented but client may not expose all

### Observed Behavior
- Run 1 verified `list_scheduled_strategies` and `get_top_movers` via direct server import
- MCP client (Cursor) tool list may not include all server tools
- No way to verify tool visibility without manual testing

### Root Cause Analysis
1. **Client configuration**: MCP client may filter or not discover all tools
2. **Tool registration**: Server registers all tools but client discovery may be incomplete
3. **No verification**: No automated check that all server tools appear in client

### Implementation Details

#### Files Updated
- ✅ `README.md` — troubleshooting note for client-side tool filtering + listing command
- ✅ `CONTRIBUTING.md` — visibility note and direct tool-list command
- ✅ `scripts/list_mcp_tools.py` — utility script to print all registered tools

#### Verification Steps
1. Check `trader/mcp/server.py` exports all tools in FastMCP `mcp.tool()` calls
2. Document in README: "For testing, if tool not in client, use `from baretrader.mcp.server import <tool>`"
3. Add helper script: `scripts/list_mcp_tools.py` to print all registered tools

### Acceptance Criteria
- ✅ README documents tool visibility and workaround
- ✅ All 32+ tools are registered in server tool factory
- ✅ TEST-PLAN notes tools verified via server import where client filtering occurred

### Testing Strategy
```python
# scripts/list_mcp_tools.py
"""List all MCP tools registered in server."""
from baretrader.mcp.server import mcp
for tool in mcp.list_tools():
    print(f"{tool.name}: {tool.description[:60]}...")
```

---

## Summary

| Issue | Status | Priority | Blocker |
|-------|--------|----------|---------|
| Strategy tools fail with `pullback_trailing` | ✅ COMPLETE | ⭐⭐⭐⭐⭐ | Resolved |
| `run_optimization` param keys | ✅ COMPLETE | ⭐⭐⭐⭐ | Resolved |
| CSV data path docs | ✅ COMPLETE | ⭐⭐⭐ | Resolved |
| MCP tool visibility | ✅ COMPLETE | ⭐⭐ | Resolved |

**Next Steps**:
1. Keep MCP contract/parity tests green in CI for regressions.
2. Continue phase planning in main roadmap document(s) for v1.2+.
