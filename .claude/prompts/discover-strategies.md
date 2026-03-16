# Discover Trading Strategies

Guided discovery workflow for finding trading strategies that work for specific goals. This prompt helps explore strategies systematically, even when you don't know what questions to ask.

## Objective

Help discover trading strategies by:
- Starting with broad questions and narrowing down
- Understanding risk vs reward trade-offs
- Optimizing for specific goals (safety, returns, etc.)
- Testing systematically across different conditions
- Documenting findings in CONTEXTS.md

## Available MCP Tools

Use these BareTrader MCP tools:
- `get_quote(symbol)` - Get current price
- `run_backtest` - Test strategies
- `compare_backtests` - Compare results
- `run_optimization` - Optimize parameters
- `show_backtest(backtest_id)` - Get detailed results

## Workflow

### Step 1: Start Broad

**User says**: "I want to trade [SYMBOL]. What strategies should I consider?"

**Actions**:
1. Call `get_quote(symbol)` to check current price
2. Test all strategy types on the symbol:
   - `run_backtest(strategy_type="trailing-stop", symbol="...", ...)`
   - `run_backtest(strategy_type="bracket", symbol="...", ...)`
   - `run_backtest(strategy_type="scale-out", symbol="...", ...)`
   - `run_backtest(strategy_type="grid", symbol="...", ...)`
3. Use same time period for fair comparison (e.g., last 12 months)
4. Call `compare_backtests([id1, id2, id3, id4])` to compare
5. Present findings:
   - Which strategy has highest Sharpe ratio?
   - Which has highest return?
   - Which has lowest drawdown?
   - Which has highest win rate?

**Document in CONTEXTS.md**: Strategy comparison results.

### Step 2: Understand Risk

**User says**: "What's the safest way to trade [SYMBOL]?"

**Actions**:
1. Focus on risk metrics: max drawdown, Sharpe ratio
2. Test conservative parameters:
   - Smaller trailing stops (lower risk)
   - Tighter bracket orders (smaller stop-loss)
3. Compare risk metrics across configurations
4. Present safest option with explanation

**Document in CONTEXTS.md**: Risk analysis, safest configurations.

### Step 3: Optimize for Goals

#### Goal: "I want steady returns with low risk"

**Actions**:
1. Focus on strategies with:
   - High Sharpe ratio (>1.5)
   - Low max drawdown (<5%)
   - Consistent win rate (>55%)
2. Use `run_optimization` with objective="sharpe_ratio"
3. Present best option with risk characteristics

#### Goal: "I want higher returns and can accept more risk"

**Actions**:
1. Focus on strategies with:
   - Higher total return potential
   - Acceptable Sharpe ratio (>1.0)
2. Test more aggressive parameters
3. Use `run_optimization` with objective="total_return_pct"
4. Present best option with risk level

**Document in CONTEXTS.md**: Optimization results for each goal.

### Step 4: Market Condition Awareness

**User says**: "How should I adjust my strategy in different market conditions?"

**Actions**:
1. Test strategies across different market regimes:
   - Trending market: Clear upward trend
   - Ranging market: Sideways movement
   - Volatile market: High volatility
2. For each condition:
   - Run backtests with same strategy
   - Compare performance metrics
   - Identify which strategies work best
3. Present findings with execution guidelines

**Document in CONTEXTS.md**: Market condition analysis.

### Step 5: Parameter Optimization

**User says**: "What's the best [PARAMETER] for [STRATEGY]?"

**Example**: "What's the best trailing stop percentage?"

**Actions**:
1. Define parameter range to test (e.g., trailing_pct: [1.5, 2.0, 2.5, 3.0, 5.0])
2. Call `run_optimization`:
   ```json
   {
     "strategy_type": "trailing-stop",
     "symbol": "AAPL",
     "start": "2024-01-01",
     "end": "2024-12-31",
     "params": {"trailing_pct": [1.5, 2.0, 2.5, 3.0, 5.0]},
     "objective": "sharpe_ratio",
     "method": "grid"
   }
   ```
3. Analyze results and identify optimal parameter
4. Validate on different period
5. Present findings with trade-offs

**Document in CONTEXTS.md**: Parameter optimization results.

### Step 6: Validation

**User says**: "Has this strategy worked consistently over time?"

**Actions**:
1. Test strategy across multiple time periods:
   - Period 1: 2024-01-01 to 2024-12-31
   - Period 2: 2023-01-01 to 2023-12-31
   - Period 3: 2022-01-01 to 2022-12-31
2. Compare metrics across periods
3. Check for consistency
4. Present findings

**Document in CONTEXTS.md**: Consistency analysis.

## Example Discovery Session

**User**: "I want to trade AAPL safely"

**Workflow**:
1. Test all strategies on AAPL (Step 1)
2. Focus on risk metrics (Step 2)
3. Optimize for low risk (Step 3)
4. Test across market conditions (Step 4)
5. Optimize parameters (Step 5)
6. Validate consistency (Step 6)
7. Present recommendation
8. Document in CONTEXTS.md

## Presenting Results

Use clear, non-technical language:

**Good**:
- "The trailing-stop strategy with a 2.5% trail is safest for AAPL"
- "You can expect about 15% returns with a maximum loss of 3%"
- "This works best when the stock is trending upward"

**Avoid**: Technical jargon without explanation.

## Documentation

After each discovery session, document in CONTEXTS.md:
- User's goal/question
- Strategies tested
- Results and comparisons
- Recommendations made
- Rationale for recommendations

## Next Steps

After discovery:
- User may want to test recommended strategy
- Consider curating portfolio if strategy meets quality thresholds
- Continue exploration based on user feedback
