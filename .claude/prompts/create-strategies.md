# Create Portfolio Strategies

Create all strategies from PORTFOLIO.md in the trading system. This sets up the initial portfolio structure.

## Objective

Create all strategies defined in PORTFOLIO.md by:
- Reading strategy definitions from PORTFOLIO.md
- Creating each strategy with correct parameters
- Verifying strategies are created successfully
- Enabling strategies for trading
- Providing summary of created strategies

## Available MCP Tools

Use these BareTrader MCP tools:
- `create_strategy` - Create new strategy
- `list_strategies` - List existing strategies
- `get_strategy(strategy_id)` - Get strategy details
- `set_strategy_enabled(strategy_id, enabled)` - Enable/disable strategy
- `get_quote(symbol)` - Get current price for validation

## Workflow

### Step 1: Read Portfolio Strategies

**Actions**:
1. Read `PORTFOLIO.md`
2. Extract all strategy definitions:
   - Symbol
   - Strategy type (trailing-stop, bracket, etc.)
   - Parameters (trailing_stop_pct, take_profit_pct, stop_loss_pct, etc.)
   - Quantity per trade
   - Entry type (market, limit, etc.)
3. Create list of strategies to create

**Output**: Display strategies to create

### Step 2: Check Existing Strategies

**Actions**:
1. Call `list_strategies` to get existing strategies
2. For each strategy in PORTFOLIO.md:
   - Check if strategy already exists (by symbol and type)
   - If exists, note strategy_id and current parameters
   - If doesn't exist, mark for creation

**Output**: Display existing vs new strategies

### Step 3: Create Strategies (Interactive)

For each strategy to create:

#### 3a: Prepare Strategy Parameters

**Actions**:
1. Extract parameters from PORTFOLIO.md:
   - `strategy_type`: trailing-stop or bracket
   - `symbol`: ticker symbol
   - `qty`: shares per trade (from PORTFOLIO.md or default 10)
   - `trailing_stop_pct`: if trailing-stop strategy
   - `take_profit_pct`: if bracket strategy
   - `stop_loss_pct`: if bracket strategy
   - `entry_price`: null (market order) or specific price
2. Validate parameters are complete
3. Get current quote to validate symbol exists

**Output**: Display strategy parameters

#### 3b: Request User Approval

**Actions**:
1. Display strategy creation proposal:
```
═══════════════════════════════════════════════════════════
CREATE STRATEGY PROPOSAL
═══════════════════════════════════════════════════════════

Symbol: NVDA
Strategy Type: trailing-stop
Parameters:
  - Trailing Stop: 5.0%
  - Quantity: 10 shares per trade
  - Entry: Market order
  - Target Allocation: 25% of portfolio

Current Price: $150.00

This strategy will:
  - Enter positions automatically on market signals
  - Use trailing stop (5%) to protect profits
  - Target 25% portfolio allocation

Approve creation? (yes/no/skip)
```

2. Wait for user approval

**Output**: User approval status

#### 3c: Create Strategy

**Actions**:
1. Call `create_strategy` with parameters
2. Verify strategy created successfully
3. Get strategy_id from response
4. Enable strategy: `set_strategy_enabled(strategy_id, true)`
5. Verify strategy is enabled

**Output**: Strategy creation result

#### 3d: Verify and Continue

**Actions**:
1. Call `get_strategy(strategy_id)` to verify
2. Compare created parameters to intended parameters
3. If mismatch, note issue and ask user how to proceed
4. Continue to next strategy

**Output**: Verification result and next strategy

### Step 4: Final Summary

**Actions**:
1. List all created strategies
2. List any strategies that already existed
3. List any strategies that failed to create
4. Display final portfolio structure

**Output**: Summary of all strategies

## Important Rules

1. **Always ask before creating**: Show strategy details and get approval
2. **Check existing strategies**: Don't duplicate existing strategies
3. **Verify after creation**: Confirm strategy was created correctly
4. **Enable strategies**: Enable strategies after creation
5. **Handle errors**: If creation fails, explain why and ask how to proceed
6. **Preserve existing**: If strategy exists with different parameters, ask user what to do

## Parameter Mapping

From PORTFOLIO.md to `create_strategy()`:

- **trailing-stop strategy**:
  - `strategy_type`: "trailing-stop"
  - `trailing_pct`: from `trailing_stop_pct` in PORTFOLIO.md
  - `qty`: from `qty` in PORTFOLIO.md (default: 10)
  - `entry_price`: null (market) or specific price

- **bracket strategy**:
  - `strategy_type`: "bracket"
  - `take_profit`: from `take_profit_pct` in PORTFOLIO.md
  - `stop_loss`: from `stop_loss_pct` in PORTFOLIO.md
  - `qty`: from `qty` in PORTFOLIO.md (default: 10)
  - `entry_price`: null (market) or specific price

## Example Interaction

```
Agent: "I found 10 strategies in PORTFOLIO.md to create.
        Starting with NVDA trailing-stop strategy...

═══════════════════════════════════════════════════════════
CREATE STRATEGY PROPOSAL #1 of 10
═══════════════════════════════════════════════════════════

Symbol: NVDA
Strategy Type: trailing-stop
Parameters:
  - Trailing Stop: 5.0%
  - Quantity: 10 shares per trade
  - Entry: Market order
  - Target Allocation: 25% of portfolio

Current Price: $150.00

This strategy will:
  - Enter positions automatically on market signals
  - Use trailing stop (5%) to protect profits
  - Target 25% portfolio allocation

Approve creation? (yes/no/skip)"

User: "yes"

Agent: "Creating strategy... [creates strategy]
        Strategy created successfully! ID: abc123
        Strategy enabled and ready for trading.
        
        Moving to next strategy: MSFT trailing-stop..."
```

## Error Handling

- **Strategy already exists**: Show existing strategy details, ask if should update or skip
- **Invalid parameters**: Show error, suggest corrections
- **Symbol not found**: Verify symbol is correct, suggest alternatives
- **Creation fails**: Show error details, ask if should retry or skip
- **Enable fails**: Note strategy created but not enabled, ask if should enable manually

## Completion Criteria

All strategies from PORTFOLIO.md are:
- Created in the trading system
- Enabled and ready for trading
- Verified with correct parameters
- Listed in final summary
