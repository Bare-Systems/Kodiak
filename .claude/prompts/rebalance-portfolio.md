# Rebalance Portfolio

Interactive workflow for rebalancing the trading account to match the target portfolio allocation defined in PORTFOLIO.md. This is a step-by-step, user-approved process where each trade is explained and approved before execution.

## Objective

Rebalance the trading account to match target allocations in PORTFOLIO.md by:
- Comparing current positions to target allocations
- Calculating required trades to achieve targets
- Presenting each trade with full context for user approval
- Executing trades one at a time with user confirmation
- Continuing until portfolio is fully rebalanced

## Available MCP Tools

Use these BareTrader MCP tools:
- `get_balance` - Get account balance and equity
- `get_positions` - Get current open positions
- `list_strategies` - List active strategies
- `get_strategy(strategy_id)` - Get strategy details
- `get_quote(symbol)` - Get current price for calculations
- `create_strategy` - Create new strategy
- `remove_strategy(strategy_id)` - Remove strategy
- `set_strategy_enabled(strategy_id, enabled)` - Enable/disable strategy

## Workflow

### Step 1: Read Portfolio Targets

**Actions**:
1. Read `PORTFOLIO.md` to understand target allocations
2. Extract target allocation table with symbols, strategies, and percentages
3. Note any special instructions or risk management rules

**Output**: Display target portfolio allocation summary

### Step 2: Get Current Account State

**Actions**:
1. Call `get_balance` to get account balance and equity
2. Call `get_positions` to get current open positions
3. Call `list_strategies` to get active strategies
4. For each active strategy, call `get_strategy(strategy_id)` for details

**Output**: Display current account state:
- Account balance and equity
- Current positions (symbol, quantity, current value, P/L)
- Active strategies (symbol, type, enabled status)

### Step 3: Calculate Target Allocations

**Actions**:
1. Calculate target dollar amounts for each symbol/strategy:
   - Target $ = (Target %) × (Current Account Equity)
2. For each symbol/strategy, calculate:
   - Current value (from positions or strategies)
   - Target value (from allocation %)
   - Difference (target - current)
   - Required action (buy/sell/create/remove)

**Output**: Display rebalancing plan:
- Symbol/Strategy | Current Value | Target Value | Difference | Action

### Step 4: Prioritize Rebalancing Actions

**Actions**:
1. Sort actions by priority:
   - **High Priority**: Large differences (>5% of portfolio)
   - **Medium Priority**: Medium differences (2-5% of portfolio)
   - **Low Priority**: Small differences (<2% of portfolio)
2. Group actions:
   - **Create strategies** (new positions needed)
   - **Increase positions** (buy more)
   - **Decrease positions** (sell some)
   - **Remove strategies** (close positions)

**Output**: Display prioritized action list

### Step 5: Execute Rebalancing (Interactive Loop)

For each action in priority order:

#### 5a: Prepare Trade Details

**Actions**:
1. Get current quote: `get_quote(symbol)`
2. Calculate required quantity:
   - For buys: `qty = (target_value - current_value) / current_price`
   - For sells: `qty = (current_value - target_value) / current_price`
3. Get strategy details if strategy exists
4. Calculate expected impact:
   - New position value
   - New allocation percentage
   - Portfolio impact

**Output**: Display trade proposal with:
```
═══════════════════════════════════════════════════════════
TRADE PROPOSAL #X of Y
═══════════════════════════════════════════════════════════

Symbol: [SYMBOL]
Strategy: [strategy_type]
Action: [BUY/SELL/CREATE STRATEGY/REMOVE STRATEGY]

Current State:
  - Current Position: [qty] shares @ $[price] = $[value]
  - Current Allocation: [X]% of portfolio
  - Current Strategy: [status/details]

Target State:
  - Target Allocation: [X]% of portfolio
  - Target Value: $[target_value]
  - Required Change: $[difference]

Trade Details:
  - Action: [BUY/SELL] [qty] shares
  - Current Price: $[price] (bid: $[bid], ask: $[ask])
  - Trade Value: $[trade_value]
  - Expected Fees: ~$[estimated_fees]

After Trade:
  - New Position: [new_qty] shares = $[new_value]
  - New Allocation: [X]% of portfolio
  - Remaining Cash: $[cash_after]

Reason:
  - [Why this trade is needed]
  - [How it moves toward target allocation]

Risk Considerations:
  - [Any risks or concerns]

═══════════════════════════════════════════════════════════
```

#### 5b: Request User Approval

**Actions**:
1. Present trade proposal clearly
2. Ask: "Approve this trade? (yes/no/modify)"
3. If "modify", ask what to change and recalculate
4. Wait for explicit approval before proceeding

**Output**: User approval status

#### 5c: Execute Approved Trade

**Actions**:
1. If creating new strategy:
   - Call `create_strategy` with parameters from PORTFOLIO.md
   - Verify strategy created successfully
2. If buying/selling:
   - Check if strategy exists, create if needed
   - Strategy will handle order execution automatically
   - Or use `place_order` if manual execution needed
3. If removing strategy:
   - Call `remove_strategy(strategy_id)`
   - Verify strategy removed
4. Update current state tracking

**Output**: Trade execution result and updated state

#### 5d: Verify and Continue

**Actions**:
1. Refresh account state: `get_balance`, `get_positions`
2. Recalculate allocations
3. Check if rebalancing is complete (all within tolerance, e.g., ±1%)
4. If not complete, continue to next action
5. If complete, display final portfolio state

**Output**: Updated state and next action or completion message

### Step 6: Final Verification

**Actions**:
1. Get final account state
2. Compare final allocations to targets
3. Calculate any remaining differences
4. Display final portfolio summary:
   - Target vs Actual allocations
   - Any positions still outside tolerance
   - Recommendations for future rebalancing

**Output**: Final portfolio state and summary

## Important Rules

1. **Always ask before trading**: Never execute a trade without explicit user approval
2. **Show full context**: Always display current state, target state, and expected impact
3. **Explain reasoning**: Always explain why each trade is needed
4. **One trade at a time**: Execute trades sequentially, not in batches
5. **Verify after each trade**: Refresh account state after each execution
6. **Handle errors gracefully**: If a trade fails, explain why and ask how to proceed
7. **Respect tolerance**: Consider rebalancing complete when all positions are within ±1% of target
8. **Preserve strategies**: Don't remove strategies unless explicitly needed for rebalancing

## Tolerance Levels

- **Exact match**: Within ±0.5% of target allocation
- **Acceptable**: Within ±1% of target allocation
- **Needs rebalancing**: Outside ±1% of target allocation
- **Critical**: Outside ±5% of target allocation (high priority)

## Example Interaction Flow

```
Agent: "I've analyzed your portfolio. Current equity: $100,000. 
        Target allocation shows NVDA should be 25% ($25,000).
        Current NVDA position: $15,000 (15%).
        Need to increase by $10,000.

═══════════════════════════════════════════════════════════
TRADE PROPOSAL #1 of 5
═══════════════════════════════════════════════════════════
Symbol: NVDA
Strategy: trailing-stop (5%)
Action: BUY shares to increase position

Current State:
  - Current Position: 10 shares @ $150.00 = $1,500
  - Current Allocation: 15% of portfolio
  - Current Strategy: Active trailing-stop

Target State:
  - Target Allocation: 25% of portfolio
  - Target Value: $25,000
  - Required Change: +$10,000

Trade Details:
  - Action: BUY ~67 shares
  - Current Price: $150.00 (bid: $149.95, ask: $150.05)
  - Trade Value: ~$10,000
  - Expected Fees: ~$1

After Trade:
  - New Position: ~77 shares = $25,000
  - New Allocation: 25% of portfolio
  - Remaining Cash: $75,000

Reason:
  - NVDA is under-allocated (15% vs 25% target)
  - This is the highest priority rebalancing action
  - Increases exposure to highest-return strategy

Risk Considerations:
  - NVDA is volatile, but has proven strong performance
  - Trailing stop (5%) provides risk management

Approve this trade? (yes/no/modify)"

User: "yes"

Agent: "Trade approved. Executing... [executes trade]
        Trade completed successfully.
        Updated NVDA position: 77 shares @ $150.00 = $11,550
        (Note: Strategy will handle additional buys automatically)
        
        Moving to next rebalancing action..."
```

## Error Handling

- **Insufficient funds**: Explain shortfall and suggest alternatives (reduce other positions, partial trade)
- **Strategy creation fails**: Show error details, suggest manual creation
- **Price moved**: Recalculate with new price and ask for approval again
- **Market closed**: Note that trades will execute when market opens
- **Position limits**: Check if position size exceeds limits, adjust if needed

## Completion Criteria

Rebalancing is complete when:
- All positions are within ±1% of target allocations
- All required strategies are active
- Account state matches target portfolio structure
- User confirms satisfaction with final state
