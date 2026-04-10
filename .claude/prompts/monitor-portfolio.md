# Monitor Portfolio

Check current portfolio state against target allocations and identify any rebalancing needs. This is a read-only analysis that doesn't execute trades.

## Objective

Monitor the portfolio by:
- Comparing current positions to target allocations
- Identifying positions that need rebalancing
- Calculating portfolio performance metrics
- Providing recommendations for rebalancing

## Available MCP Tools

Use these Kodiak MCP tools:
- `get_balance` - Get account balance and equity
- `get_positions` - Get current open positions
- `get_portfolio` - Get detailed portfolio summary
- `list_strategies` - List active strategies
- `get_strategy(strategy_id)` - Get strategy details
- `get_quote(symbol)` - Get current prices
- `get_today_pnl` - Get today's P/L

## Workflow

### Step 1: Read Portfolio Targets

**Actions**:
1. Read `PORTFOLIO.md` to understand target allocations
2. Extract target allocation table
3. Note any risk management rules

**Output**: Display target allocations summary

### Step 2: Get Current Portfolio State

**Actions**:
1. Call `get_balance` for account balance and equity
2. Call `get_positions` for current positions
3. Call `get_portfolio` for detailed portfolio summary
4. Call `list_strategies` for active strategies
5. Call `get_today_pnl` for today's performance

**Output**: Display current portfolio state

### Step 3: Calculate Allocation Comparison

**Actions**:
1. For each target allocation:
   - Calculate target dollar amount: `target_value = target_% × equity`
   - Find current position value (from positions or strategies)
   - Calculate difference: `difference = current_value - target_value`
   - Calculate deviation: `deviation_% = (current_value / target_value - 1) × 100`
2. Identify positions outside tolerance (±1%)

**Output**: Display allocation comparison table:
```
Portfolio Allocation Status
═══════════════════════════════════════════════════════════
Symbol    Target%  Target$   Current$  Difference  Status
───────────────────────────────────────────────────────────
NVDA      25%      $25,000   $24,500   -$500      ✅ OK
MSFT      15%      $15,000   $16,200   +$1,200    ⚠️ High
XLK       15%      $15,000   $14,800   -$200      ✅ OK
...
```

### Step 4: Analyze Performance

**Actions**:
1. Calculate portfolio-level metrics:
   - Total portfolio value
   - Total unrealized P/L
   - Today's P/L
   - Portfolio return %
2. Calculate position-level metrics:
   - Individual position P/L
   - Position return %
   - Position weight vs target

**Output**: Display performance summary

### Step 5: Identify Rebalancing Needs

**Actions**:
1. Flag positions needing rebalancing:
   - **Critical**: Outside ±5% of target
   - **Needs Attention**: Outside ±1% of target
   - **OK**: Within ±1% of target
2. Calculate required trades:
   - Buy requirements (under-allocated)
   - Sell requirements (over-allocated)
   - Strategy creation/removal needs

**Output**: Display rebalancing recommendations

### Step 6: Provide Recommendations

**Actions**:
1. Summarize findings
2. Prioritize actions:
   - High priority (critical deviations)
   - Medium priority (moderate deviations)
   - Low priority (minor deviations)
3. Suggest next steps:
   - Run `/rebalance-portfolio` if needed
   - Monitor specific positions
   - Review strategy performance

**Output**: Display recommendations and next steps

## Output Format

```
═══════════════════════════════════════════════════════════
PORTFOLIO MONITORING REPORT
═══════════════════════════════════════════════════════════

Account Summary:
  - Account Equity: $105,000
  - Cash Available: $5,000
  - Total Positions Value: $100,000
  - Unrealized P/L: +$5,000 (+5.0%)
  - Today's P/L: +$500 (+0.5%)

Allocation Status:
  Symbol    Target%  Target$   Current$  Difference  Status
  ───────────────────────────────────────────────────────────
  NVDA      25%      $26,250   $28,000   +$1,750     ⚠️ High
  MSFT      15%      $15,750   $15,200   -$550       ✅ OK
  XLK       15%      $15,750   $14,500   -$1,250     ⚠️ Low
  GOOGL     10%      $10,500   $10,800   +$300       ✅ OK
  AMZN      10%      $10,500   $10,200   -$300       ✅ OK
  XLI        8%      $8,400    $8,600    +$200       ✅ OK
  XLF        7%      $7,350    $7,100    -$250       ✅ OK
  XLP        5%      $5,250    $5,400    +$150       ✅ OK
  AEM        3%      $3,150    $3,200    +$50        ✅ OK
  GDX        2%      $2,100    $2,000    -$100       ✅ OK

Rebalancing Needs:
  ⚠️ HIGH PRIORITY:
    - NVDA: Over-allocated by $1,750 (6.7% above target)
    - XLK: Under-allocated by $1,250 (7.9% below target)
  
  ✅ ACCEPTABLE:
    - All other positions within ±1% tolerance

Recommendations:
  1. Reduce NVDA position by ~$1,750 (sell ~12 shares)
  2. Increase XLK position by ~$1,250 (buy ~6 shares)
  3. Run `/rebalance-portfolio` to execute rebalancing
  4. Monitor NVDA closely (strong performance driving over-allocation)

Next Steps:
  - Run `/rebalance-portfolio` to rebalance
  - Or wait if expecting continued NVDA gains
```

## Tolerance Levels

- **✅ OK**: Within ±1% of target allocation
- **⚠️ Needs Attention**: Outside ±1% but within ±5%
- **🔴 Critical**: Outside ±5% of target allocation

## When to Run

- Daily: Quick check of portfolio state
- Weekly: Detailed monitoring and analysis
- After significant market moves
- Before scheduled rebalancing
- After strategy changes
