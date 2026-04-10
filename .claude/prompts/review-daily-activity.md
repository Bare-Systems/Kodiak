# Review Daily Portfolio Activity

Review the last day of trading activity, evaluate strategy performance, and identify adjustments needed. Present recommendations for user approval before executing any changes.

## Objective

Review and optimize the portfolio by:
- Analyzing yesterday's trading activity and performance
- Evaluating current strategies against their expected behavior
- Identifying underperforming strategies or missing opportunities
- Proposing strategy adjustments, additions, or removals
- Getting user approval before executing any changes

## Available MCP Tools

Use these Kodiak MCP tools:
- `get_trade_history(symbol=None, limit=100)` - Get recent trades (last day)
- `get_today_pnl` - Get today's realized P/L
- `analyze_performance(symbol=None, days=1, limit=100)` - Analyze performance metrics
- `get_balance` - Account balance and equity
- `get_positions` - Current open positions
- `get_portfolio` - Full portfolio summary
- `list_strategies` - List all configured strategies
- `get_strategy(strategy_id)` - Get strategy details
- `get_quote(symbol)` - Get current prices
- `create_strategy` - Create new strategy
- `remove_strategy(strategy_id)` - Remove strategy
- `set_strategy_enabled(strategy_id, enabled)` - Enable/disable strategy
- `pause_strategy(strategy_id)` - Pause strategy
- `resume_strategy(strategy_id)` - Resume strategy

## Workflow

### Step 1: Gather Yesterday's Activity

**Actions**:
1. Call `get_trade_history(limit=100)` to get recent trades
2. Filter trades to yesterday's date (or last trading day if weekend)
3. Call `get_today_pnl` for realized P/L
4. Call `analyze_performance(days=1, limit=100)` for performance metrics
5. Group trades by symbol and strategy

**Output**: Display yesterday's activity summary:
```
═══════════════════════════════════════════════════════════
YESTERDAY'S TRADING ACTIVITY
═══════════════════════════════════════════════════════════

Date: [YYYY-MM-DD]
Total Trades: [X]
Realized P/L: $[amount] ([+/-]X.X%)

Trades by Symbol:
  - [SYMBOL]: [X] trades, P/L: $[amount]
  - ...

Trades by Strategy:
  - [strategy_id]: [X] trades, P/L: $[amount]
  - ...
```

### Step 2: Get Current Portfolio State

**Actions**:
1. Call `get_balance` for account equity and cash
2. Call `get_positions` for current positions
3. Call `get_portfolio` for detailed portfolio summary
4. Call `list_strategies` for all strategies
5. For each active strategy, call `get_strategy(strategy_id)` for details

**Output**: Display current state:
- Account equity and cash
- Open positions (symbol, quantity, value, unrealized P/L)
- Active strategies (symbol, type, enabled status, phase)
- Portfolio allocation

### Step 3: Evaluate Strategy Performance

**Actions**:
1. For each active strategy:
   - Get strategy details (type, symbol, phase, entry/exit orders)
   - Check if strategy executed trades yesterday
   - Compare actual behavior vs expected behavior:
     - **Trailing stop**: Should have moved stop up, did it?
     - **Bracket**: Should have hit take-profit or stop-loss if price moved enough
     - **Scale-out**: Should have sold tranches at profit targets
     - **Grid**: Should have executed buy/sell orders at grid levels
   - Calculate strategy P/L (from trades or position)
   - Identify any issues:
     - Strategy not executing (stuck in entry phase?)
     - Strategy executing too frequently (overtrading?)
     - Strategy missing targets (parameters wrong?)
     - Strategy underperforming vs expectations

2. Check for missing strategies:
   - Read `PORTFOLIO.md` to see target allocations
   - Compare target symbols vs active strategies
   - Identify symbols that should have strategies but don't

**Output**: Display strategy evaluation:
```
═══════════════════════════════════════════════════════════
STRATEGY PERFORMANCE EVALUATION
═══════════════════════════════════════════════════════════

Active Strategies:
  [strategy_id] - [SYMBOL] ([strategy_type])
    Status: [enabled/paused/disabled]
    Phase: [entry/monitoring/exit/complete]
    Yesterday's Activity: [X trades / No trades]
    P/L: $[amount] ([+/-]X.X%)
    Issues: [none / stuck in entry / missing targets / etc.]
    Recommendation: [keep / adjust / pause / remove]

Missing Strategies (from PORTFOLIO.md):
  - [SYMBOL]: Should have [strategy_type] strategy
  - ...
```

### Step 4: Identify Adjustments Needed

**Actions**:
1. Categorize issues:
   - **Critical**: Strategy stuck, not executing, or losing money unexpectedly
   - **Needs Adjustment**: Strategy working but parameters may be suboptimal
   - **Missing**: Should have strategy but doesn't
   - **Underperforming**: Strategy executing but not meeting expectations

2. For each issue, determine recommended action:
   - **Remove strategy**: If stuck, not working, or no longer needed
   - **Pause strategy**: If temporarily not suitable for current market
   - **Adjust strategy**: Change parameters (trailing %, take-profit, etc.)
   - **Create strategy**: Add missing strategy from PORTFOLIO.md
   - **Enable strategy**: If disabled but should be active
   - **Disable strategy**: If active but shouldn't be

3. Prioritize actions:
   - **High Priority**: Critical issues, missing strategies
   - **Medium Priority**: Parameter adjustments, enable/disable
   - **Low Priority**: Minor optimizations

**Output**: Display recommended adjustments:
```
═══════════════════════════════════════════════════════════
RECOMMENDED ADJUSTMENTS
═══════════════════════════════════════════════════════════

🔴 HIGH PRIORITY:
  1. [Action]: [Description]
     - Current: [state]
     - Issue: [problem]
     - Proposed: [change]
     - Expected Impact: [benefit]

  2. ...

🟡 MEDIUM PRIORITY:
  1. [Action]: [Description]
     ...

🟢 LOW PRIORITY:
  1. [Action]: [Description]
     ...
```

### Step 5: Present Recommendations and Get Approval

**Actions**:
1. Summarize findings:
   - Yesterday's performance summary
   - Key issues identified
   - Recommended actions

2. For each recommended action, present:
   - **What**: Clear description of the change
   - **Why**: Reason for the change (data-driven)
   - **Impact**: Expected effect on portfolio
   - **Risk**: Any risks or considerations

3. Ask user: "Would you like me to proceed with these adjustments? (yes/no/modify)"

**Output**: Display summary and request approval:
```
═══════════════════════════════════════════════════════════
DAILY REVIEW SUMMARY
═══════════════════════════════════════════════════════════

Yesterday's Performance:
  - Total Trades: [X]
  - Realized P/L: $[amount] ([+/-]X.X%)
  - Best Performer: [SYMBOL] (+$[amount])
  - Worst Performer: [SYMBOL] (-$[amount])

Current Portfolio:
  - Equity: $[amount]
  - Open Positions: [X]
  - Active Strategies: [X]
  - Unrealized P/L: $[amount] ([+/-]X.X%)

Key Findings:
  1. [Finding 1]
  2. [Finding 2]
  3. [Finding 3]

Recommended Actions:
  [List of actions with priorities]

Would you like me to proceed with these adjustments? (yes/no/modify)
```

### Step 6: Execute Approved Changes (Interactive)

If user approves, execute changes one at a time with confirmation:

#### 6a: Present Each Change

**Actions**:
1. For each approved action:
   - Display change details clearly
   - Show current state vs proposed state
   - Explain expected impact
   - Ask: "Execute this change? (yes/no/skip)"

**Output**: Display change proposal:
```
═══════════════════════════════════════════════════════════
CHANGE PROPOSAL #X of Y
═══════════════════════════════════════════════════════════

Action: [CREATE STRATEGY / REMOVE STRATEGY / PAUSE STRATEGY / ENABLE STRATEGY / etc.]

Details:
  - Strategy: [strategy_id] ([SYMBOL])
  - Current State: [description]
  - Proposed State: [description]
  - Reason: [why this change is needed]
  - Expected Impact: [what will change]

Execute this change? (yes/no/skip)
```

#### 6b: Execute Change

**Actions**:
1. If creating strategy:
   - Call `create_strategy` with parameters
   - Verify strategy created successfully
2. If removing strategy:
   - Call `remove_strategy(strategy_id)`
   - Verify strategy removed
3. If pausing/resuming:
   - Call `pause_strategy` or `resume_strategy()`
   - Verify status changed
4. If enabling/disabling:
   - Call `set_strategy_enabled(strategy_id, enabled)`
   - Verify status changed
5. Refresh state after each change

**Output**: Display execution result and updated state

#### 6c: Continue or Complete

**Actions**:
1. After each change, refresh portfolio state
2. Continue to next change if more remain
3. If all changes complete, display final summary

**Output**: Final portfolio state and summary

### Step 7: Final Summary

**Actions**:
1. Get final portfolio state
2. Compare before vs after
3. Display what changed
4. Note any remaining issues or future recommendations

**Output**: Final summary:
```
═══════════════════════════════════════════════════════════
REVIEW COMPLETE
═══════════════════════════════════════════════════════════

Changes Executed:
  ✅ [Change 1]
  ✅ [Change 2]
  ⏭️  [Change 3] - Skipped by user

Current Portfolio State:
  - Active Strategies: [X]
  - Open Positions: [X]
  - Account Equity: $[amount]

Remaining Issues:
  - [Issue 1] - Monitor and review tomorrow
  - [Issue 2] - Consider addressing next week

Next Review:
  - Run this review again tomorrow
  - Monitor [specific strategies] closely
  - Consider [future action] if [condition]
```

## Important Rules

1. **Always ask before changing**: Never execute a change without explicit user approval
2. **One change at a time**: Present and execute changes sequentially
3. **Show data**: Always reference actual trade data and performance metrics
4. **Explain reasoning**: Explain why each change is recommended
5. **Respect user choice**: If user says "no" or "skip", move to next change
6. **Handle errors gracefully**: If a change fails, explain why and ask how to proceed
7. **Focus on yesterday**: This is a daily review, focus on recent activity
8. **Compare to expectations**: Evaluate strategies against their intended behavior

## Evaluation Criteria

### Strategy Health Checks

- **Entry Phase**: Has strategy been in entry phase too long? (>1 week without entry?)
- **Execution**: Is strategy executing trades as expected?
- **Performance**: Is strategy meeting profit targets or stop losses appropriately?
- **Frequency**: Is strategy trading too often (overtrading) or too rarely (missing opportunities)?
- **Parameters**: Are strategy parameters (trailing %, take-profit, etc.) appropriate for current volatility?

### Missing Strategies

- Check `PORTFOLIO.md` for target allocations
- Identify symbols that should have strategies but don't
- Consider if market conditions are suitable for adding strategies

### Performance Issues

- Compare actual P/L vs expected P/L
- Check if strategies are hitting targets or stops appropriately
- Identify strategies that are consistently underperforming

## Example Interaction Flow

```
Agent: "I've reviewed yesterday's trading activity. Here's what I found:

═══════════════════════════════════════════════════════════
YESTERDAY'S TRADING ACTIVITY
═══════════════════════════════════════════════════════════

Date: 2026-02-12
Total Trades: 5
Realized P/L: +$250 (+0.25%)

Trades:
  - NVDA: 2 trades (buy + sell), P/L: +$150
  - MSFT: 1 trade (sell), P/L: +$50
  - TSLA: 2 trades (buy + sell), P/L: +$50

Current Portfolio:
  - Equity: $100,000
  - Active Strategies: 8
  - Open Positions: 5

═══════════════════════════════════════════════════════════
STRATEGY EVALUATION
═══════════════════════════════════════════════════════════

Issues Found:
  1. NVDA trailing-stop strategy: Working well, hit trailing stop yesterday (+$150)
  2. GOOGL bracket strategy: Stuck in entry phase for 3 days, no trades
  3. Missing: XLK should have strategy per PORTFOLIO.md but doesn't
  4. TSLA grid strategy: Executing frequently but small profits, may need adjustment

═══════════════════════════════════════════════════════════
RECOMMENDED ADJUSTMENTS
═══════════════════════════════════════════════════════════

🔴 HIGH PRIORITY:
  1. CREATE STRATEGY: Add XLK trailing-stop (5%) strategy
     - Missing from portfolio, should be 15% allocation
     - Expected Impact: Increase diversification
  
  2. PAUSE STRATEGY: Pause GOOGL bracket strategy
     - Stuck in entry phase, market conditions not suitable
     - Expected Impact: Free up capital, avoid forced entry

🟡 MEDIUM PRIORITY:
  3. ADJUST STRATEGY: Increase TSLA grid spacing from 2% to 3%
     - Currently overtrading with small profits
     - Expected Impact: Fewer trades, larger profit per trade

Would you like me to proceed with these adjustments? (yes/no/modify)"

User: "yes"

Agent: "Proceeding with changes...

═══════════════════════════════════════════════════════════
CHANGE PROPOSAL #1 of 3
═══════════════════════════════════════════════════════════

Action: CREATE STRATEGY

Details:
  - Strategy: trailing-stop for XLK
  - Quantity: 10 shares
  - Trailing Stop: 5%
  - Current State: No strategy exists
  - Proposed State: Active trailing-stop strategy
  - Reason: Missing from portfolio, target allocation is 15%
  - Expected Impact: Add $15,000 exposure to XLK ETF

Execute this change? (yes/no/skip)"

User: "yes"

Agent: "Creating strategy... ✅ Strategy created successfully.
        Strategy ID: xlk-trailing-001
        Status: Enabled, Entry phase
        
        Moving to next change..."
```

## When to Run

- **Daily**: Run this review each morning to review yesterday's activity
- **After market close**: Best time to review full day's activity
- **After significant market moves**: Review if market moved significantly
- **Weekly summary**: Can run with `days=7` to review full week

## Notes

- Focus on **yesterday's activity** (or last trading day)
- Compare **actual behavior** vs **expected behavior** for each strategy
- Use **data-driven recommendations** (reference actual trades and P/L)
- **Always get approval** before executing changes
- Consider **market conditions** when recommending changes
- Reference **PORTFOLIO.md** for target allocations and strategy types
