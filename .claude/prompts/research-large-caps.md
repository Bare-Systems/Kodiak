# Research Large-Cap Stocks

Autonomous research workflow for systematically analyzing major large-cap stocks (AAPL, GOOGL, MSFT, NVDA, TSLA, etc.) to discover profitable trading strategies.

## Objective

Systematically research major large-cap stocks to:
- Identify which stocks have profitable trading strategies
- Discover optimal strategy parameters for each stock
- Build a knowledge base of validated strategies
- Document all findings in CONTEXTS.md for future reference

## Autonomous Research Principles

**You should research proactively, not wait for user direction:**

1. **Check CONTEXTS.md first** - Review what's already been researched
2. **Prioritize unexplored stocks** - Focus on stocks not yet analyzed
3. **Build on past research** - Use previous findings to guide deeper analysis
4. **Document everything** - Every backtest, comparison, and insight goes in CONTEXTS.md
5. **Continue autonomously** - After completing one stock, move to the next without asking

## Target Stocks

Focus on these major large-cap stocks (prioritize by market cap and liquidity):

**Tech Giants:**
- AAPL (Apple)
- GOOGL/GOOG (Google/Alphabet)
- MSFT (Microsoft)
- NVDA (NVIDIA)
- META (Meta/Facebook)
- AMZN (Amazon)

**Other Large Caps:**
- TSLA (Tesla)
- JPM (JPMorgan Chase)
- V (Visa)
- JNJ (Johnson & Johnson)
- WMT (Walmart)

## Research Workflow

### Step 1: Review Past Research

**Before starting, always:**
1. Read CONTEXTS.md to see what's been researched
2. Identify which stocks from the target list haven't been analyzed
3. Note any patterns or insights from previous research
4. Prioritize stocks that haven't been tested yet

### Step 2: Select Stock to Research

**Selection criteria (in order):**
1. Stocks not yet in CONTEXTS.md
2. Stocks with partial research (complete the analysis)
3. Stocks with old research (re-validate with recent data)
4. Stocks showing interesting patterns (deep dive)

**If all stocks are researched:**
- Re-test with different time periods
- Optimize parameters further
- Compare across stocks to find best performers

### Step 3: Initial Analysis

For each selected stock:

1. **Get current quote** - `get_quote(symbol)` to check liquidity
2. **Test all available strategies**:
   - Trailing-stop (5% default)
   - Bracket (10% TP, 5% SL default)
   - Note: Scale-out and grid may not be available for backtesting
3. **Use consistent time period** - Last 12 months (or full year if available)
4. **Compare results** - `compare_backtests([id1, id2, ...])`

### Step 4: Strategy Optimization

For the best-performing strategy:

1. **Run parameter optimization**:
   ```python
   run_optimization(
       strategy_type="bracket",  # or "trailing-stop"
       symbol="AAPL",
       start="2024-01-01",
       end="2024-12-31",
       params={
           "take_profit": [5, 7.5, 10, 12.5, 15],
           "stop_loss": [3, 5, 7, 10]
       },
       objective="sharpe_ratio",  # or "total_return_pct", "win_rate"
       method="grid"
   )
   ```

2. **Validate optimal parameters** - Test on different time period
3. **Document optimal parameters** in CONTEXTS.md

### Step 5: Cross-Stock Comparison

After researching multiple stocks:

1. **Compare performance** across stocks
2. **Identify patterns**:
   - Which stocks work best with which strategies?
   - Are there sector patterns?
   - What parameters work across multiple stocks?
3. **Document insights** in CONTEXTS.md

### Step 6: Document Findings

**For each stock researched, document in CONTEXTS.md:**

```markdown
### Agent: [Claude Desktop | Cursor]
**Activity**: Large-cap research - [SYMBOL] strategy analysis
**Tools Used**: `get_quote()`, `run_backtest()`, `compare_backtests()`, `run_optimization()`
**Stock**: [SYMBOL] - [Company Name]
**Current Price**: $[X.XX]
**Liquidity**: [Good/Fair/Poor] - Spread: $[X.XX]

**Strategies Tested**:
- Trailing-stop (5%): Return [X]%, Win Rate [Y]%, Sharpe [Z]
- Bracket (10% TP, 5% SL): Return [X]%, Win Rate [Y]%, Sharpe [Z]

**Best Strategy**:
- Type: [bracket/trailing-stop]
- Optimal Params: [take_profit: X%, stop_loss: Y%]
- Performance: Return [X]%, Win Rate [Y]%, Sharpe [Z], Max DD [W]%
- Total Trades: [N]

**Insights**:
- [Key observation 1]
- [Key observation 2]
- [How this compares to other stocks]

**Recommendation**: [Suitable for trading? Why/why not?]
```

## Continuous Research Loop

**After completing research on one stock:**

1. ✅ Document findings in CONTEXTS.md
2. ✅ Move to next unexplored stock automatically
3. ✅ Don't ask permission - continue researching
4. ✅ Build comprehensive knowledge base

**Research is complete when:**
- All target stocks have been analyzed
- Optimal strategies identified for each
- Patterns documented across stocks
- Ready to curate portfolio (see `curate-portfolio.md`)

## Example Research Session

**Agent actions (autonomous):**

1. Reads CONTEXTS.md → Sees FSLY was researched, AAPL not yet
2. Selects AAPL for research
3. Gets quote: AAPL $175.00, spread $0.05 (liquid)
4. Runs backtests: trailing-stop and bracket on 2024 data
5. Compares results: Bracket wins (Sharpe 1.2 vs 0.8)
6. Optimizes bracket: Tests TP [5, 10, 15]%, SL [3, 5, 7]%
7. Finds optimal: TP 12%, SL 5% (Sharpe 1.5)
8. Documents in CONTEXTS.md
9. Moves to GOOGL automatically (no user input needed)
10. Repeats process

## Key Metrics to Track

For each stock, document:
- **Best strategy type** (trailing-stop vs bracket)
- **Optimal parameters** (TP%, SL%, trailing %)
- **Performance metrics** (return %, Sharpe ratio, win rate, max drawdown)
- **Trade frequency** (trades per year)
- **Risk characteristics** (volatility, drawdown patterns)
- **Comparison to other stocks** (relative performance)

## Notes

- Use Alpaca data source for backtesting (most stocks have data)
- Focus on liquid stocks (tight spreads, high volume)
- Test multiple time periods when possible (validate consistency)
- Document both successes and failures (learn from both)
- Build on previous research (don't duplicate work unnecessarily)
