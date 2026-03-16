# Explore BareTrader Backtesting

Comprehensive exploration of BareTrader backtesting capabilities using MCP tools. This prompt guides systematic testing of strategies across different symbols, time periods, and parameters.

## Objective

Help explore backtesting capabilities by:
- Understanding available strategies and their purposes
- Testing strategies across different conditions
- Asking sophisticated questions about performance
- Documenting learnings in CONTEXTS.md

## Available MCP Tools

Use these BareTrader MCP tools:
- `list_strategies` - See configured strategies
- `run_backtest` - Run backtest on historical data
- `show_backtest(backtest_id)` - Get detailed results
- `compare_backtests(backtest_ids)` - Compare multiple backtests
- `run_optimization` - Optimize parameters
- `list_indicators` - See available indicators
- `describe_indicator(name)` - Get indicator details

## Workflow

### Phase 1: Understand the Tool

1. **Check Available Strategies**
   - Call `list_strategies` to see configured strategies
   - Call `list_indicators` to see available indicators
   - Understand strategy types:
     - `trailing-stop`: Rides trends, locks in gains
     - `bracket`: Take-profit AND stop-loss
     - `scale-out`: Sells portions at progressive targets
     - `grid`: Buys/sells at fixed price intervals

2. **Understand Key Metrics**
   - **Sharpe Ratio**: Risk-adjusted returns (higher is better, >1.0 is good)
   - **Win Rate**: Percentage of winning trades (>50% is good)
   - **Total Return %**: Overall return (context matters)
   - **Max Drawdown**: Largest peak-to-trough decline (lower is better)
   - **Profit Factor**: Gross profit / gross loss (>1.0 means profitable)

3. **Learn About Market Conditions**
   - **Trending**: Clear upward or downward trend
   - **Ranging**: Sideways movement, bounded range
   - **Volatile**: Large price swings, high uncertainty

### Phase 2: Test Different Approaches

1. **Test All Strategy Types on Same Symbol**
   - Pick a symbol (e.g., "AAPL")
   - Test trailing-stop, bracket, scale-out, grid on same symbol
   - Use same time period (e.g., start="2024-01-01", end="2024-12-31")
   - Compare results using `compare_backtests`
   - Document which performs best and why

2. **Test Same Strategy Across Different Symbols**
   - Pick a strategy (e.g., trailing-stop with trailing_pct=2.5)
   - Test on multiple symbols: "AAPL", "SPY", "TSLA", "GOOGL"
   - Same time period for fair comparison
   - Identify which symbols work best with this strategy

3. **Test Same Strategy Across Different Time Periods**
   - Pick strategy and symbol
   - Test on different periods:
     - Bull market: start="2023-01-01", end="2023-12-31"
     - Bear market: start="2022-01-01", end="2022-12-31"
     - Volatile: start="2020-03-01", end="2020-12-31"
   - Document how strategy performs in different conditions

4. **Test Parameter Variations**
   - Pick a strategy (e.g., trailing-stop)
   - Test different parameter values:
     - `trailing_pct: [1.5, 2.0, 2.5, 3.0, 5.0]`
   - Use `run_optimization` for systematic testing
   - Identify optimal parameter range

### Phase 3: Ask Sophisticated Questions

Guide exploration by asking:

1. **"Which strategy performs best in trending markets?"**
   - Test all strategies during trending periods
   - Compare Sharpe ratios and win rates

2. **"What's the optimal trailing stop percentage for tech stocks?"**
   - Test trailing-stop on multiple tech stocks
   - Use optimization to find optimal range

3. **"How does this strategy perform during market crashes?"**
   - Test strategies during volatile/crash periods
   - Analyze drawdowns and recovery

4. **"What's the risk/reward profile of this configuration?"**
   - Calculate risk metrics: max drawdown, Sharpe ratio
   - Calculate reward metrics: total return, win rate

5. **"Which symbols show consistent performance with this strategy?"**
   - Test strategy on multiple symbols
   - Look for consistent Sharpe ratios and win rates

### Phase 4: Document Learnings

After each exploration session, document in CONTEXTS.md:

```markdown
## YYYY-MM-DD

### Agent: Claude Desktop
**Activity**: Comprehensive backtesting exploration
**Tools Used**: [List MCP tools called]
**Learnings**:
- [Discovery 1]
- [Discovery 2]

**Successful Strategy Test**:
- Strategy: trailing-stop on AAPL
- Params: trailing_pct=2.5
- Results: Sharpe 1.8, Return 15.2%, Win Rate 62.5%

**Questions Explored**:
- [Question 1]
- [Answer/Discovery]
```

## Example Exploration

1. Call `get_status` to verify connection
2. Call `list_strategies` to see available strategies
3. Call `run_backtest(strategy_type="trailing-stop", symbol="AAPL", start="2024-01-01", end="2024-12-31", trailing_pct=2.5)`
4. Wait for backtest to complete, note backtest_id
5. Call `show_backtest(backtest_id)` to get detailed results
6. Extract metrics: Sharpe ratio, return %, win rate
7. Document findings in CONTEXTS.md

## Tips

- Start with one symbol and one strategy type
- Test systematically rather than randomly
- Focus on understanding metrics (Sharpe ratio, win rate)
- Document everything - patterns emerge over time
- Use optimization tools for parameter tuning

## Next Steps

After exploration:
- Review CONTEXTS.md for patterns
- Identify promising strategies for further testing
- Consider curating portfolio if strategies meet quality thresholds
