# Portfolio Status

Get a comprehensive overview of current portfolio state, positions, strategies, and performance. Quick status check without detailed analysis.

## Objective

Provide a quick overview of portfolio status by:
- Showing account balance and equity
- Listing all positions with current values
- Showing active strategies
- Displaying performance metrics
- Highlighting any issues or alerts

## Available MCP Tools

Use these Kodiak MCP tools:
- `get_balance` - Get account balance
- `get_positions` - Get current positions
- `get_portfolio` - Get portfolio summary
- `list_strategies` - List active strategies
- `get_today_pnl` - Get today's P/L
- `get_status` - Get engine status

## Workflow

### Step 1: Get Account Status

**Actions**:
1. Call `get_status` to check engine status
2. Call `get_balance` for account balance and equity
3. Call `get_today_pnl` for today's performance

**Output**: Display account status

### Step 2: Get Positions

**Actions**:
1. Call `get_positions` for all open positions
2. For each position, display:
   - Symbol
   - Quantity
   - Current price
   - Current value
   - Unrealized P/L
   - P/L percentage

**Output**: Display positions table

### Step 3: Get Strategies

**Actions**:
1. Call `list_strategies` for all strategies
2. For each strategy, display:
   - Symbol
   - Strategy type
   - Enabled status
   - Phase (entering/exiting/holding)

**Output**: Display strategies table

### Step 4: Get Portfolio Summary

**Actions**:
1. Call `get_portfolio` for detailed summary
2. Display:
   - Total portfolio value
   - Position weights
   - P/L breakdown

**Output**: Display portfolio summary

### Step 5: Quick Health Check

**Actions**:
1. Check for any alerts:
   - Engine not running
   - Positions with large losses
   - Strategies disabled
   - Account issues
2. Display any alerts or warnings

**Output**: Display health status

## Output Format

```
═══════════════════════════════════════════════════════════
PORTFOLIO STATUS
═══════════════════════════════════════════════════════════

Engine Status: ✅ Running (Paper Trading)

Account:
  - Equity: $105,000
  - Cash: $5,000
  - Buying Power: $210,000
  - Today's P/L: +$500 (+0.5%)

Positions (10):
  Symbol  Qty   Price    Value      P/L      P/L%
  ────────────────────────────────────────────────────────
  NVDA    77    $150.00  $11,550   +$1,550  +15.5%
  MSFT    50    $420.00  $21,000   +$2,000  +10.5%
  XLK     60    $220.00  $13,200   +$200    +1.5%
  GOOGL   50    $180.00  $9,000    +$500    +5.9%
  AMZN    50    $200.00  $10,000   +$300    +3.1%
  XLI     40    $120.00  $4,800    +$100    +2.1%
  XLF     60    $45.00   $2,700    -$50     -1.8%
  XLP     50    $80.00   $4,000    +$150    +3.9%
  AEM     40    $80.00   $3,200    +$200    +6.7%
  GDX     50    $40.00   $2,000    -$50     -2.4%

Active Strategies (10):
  Symbol  Strategy        Status    Phase
  ────────────────────────────────────────────
  NVDA    trailing-stop   ✅ Enabled  Holding
  MSFT    trailing-stop   ✅ Enabled  Holding
  XLK     bracket         ✅ Enabled  Holding
  GOOGL   bracket         ✅ Enabled  Holding
  AMZN    bracket         ✅ Enabled  Holding
  XLI     bracket         ✅ Enabled  Holding
  XLF     bracket         ✅ Enabled  Holding
  XLP     bracket         ✅ Enabled  Holding
  AEM     bracket         ✅ Enabled  Holding
  GDX     bracket         ✅ Enabled  Holding

Portfolio Summary:
  - Total Value: $100,000
  - Unrealized P/L: +$4,900 (+4.9%)
  - Largest Position: MSFT (21.0%)
  - Smallest Position: GDX (2.0%)

Health Status: ✅ All systems operational
```

## When to Use

- Quick portfolio check
- Before trading decisions
- Daily status review
- After market close
- Troubleshooting

## Notes

- Quick overview: Not detailed analysis
- Use `/monitor-portfolio` for detailed allocation analysis
- Use `/rebalance-portfolio` to rebalance if needed
