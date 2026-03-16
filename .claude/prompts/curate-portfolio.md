# Curate Strategy Portfolio

Review backtest results from CONTEXTS.md and add validated strategies to PORTFOLIO.md. This is a secondary process that requires extensive backtesting first.

## Objective

Curate tested strategies that meet quality thresholds and add them to PORTFOLIO.md with:
- Confidence levels
- Execution guidelines
- Risk management recommendations
- Validation history

## When to Use

Only run this workflow after:
- Extensive backtesting has been done (documented in CONTEXTS.md)
- Multiple successful backtests exist for a strategy
- Strategy shows consistent performance
- User wants to build a portfolio of validated strategies

## Available MCP Tools

Use these BareTrader MCP tools:
- `list_backtests` - List saved backtests
- `show_backtest(backtest_id)` - Get detailed results
- `compare_backtests(backtest_ids)` - Compare backtests

## Workflow

### Step 1: Review CONTEXTS.md

1. **Read CONTEXTS.md** to identify:
   - Strategies with multiple successful backtests
   - Consistent performance across time periods
   - Strategies that meet quality thresholds

2. **Look for patterns**:
   - Same strategy tested on same symbol multiple times
   - Consistent Sharpe ratios (>1.0)
   - Consistent win rates (>50%)
   - Tested across different market conditions

3. **Identify candidates**:
   - List strategies that appear promising
   - Note backtest IDs for each
   - Gather all relevant test results

### Step 2: Validate Entry Criteria

For each candidate strategy, verify:

- ✅ **Minimum 6 months historical data tested**
- ✅ **Sharpe ratio > 1.0** (prefer >1.5 for high confidence)
- ✅ **Win rate > 50%** (prefer >55% for high confidence)
- ✅ **At least 20 trades in backtest**
- ✅ **Tested across multiple market conditions**

**Action**: If criteria not met, skip this strategy or note what additional testing is needed.

### Step 3: Calculate Confidence Level

Based on validation results:

**High (80%+)**:
- Consistent across multiple periods (3+ periods)
- High Sharpe ratio (>1.5)
- Low max drawdown (<5%)
- Tested across different market regimes
- High win rate (>60%)
- At least 30+ trades total

**Medium (60-79%)**:
- Good performance but some variability
- Moderate Sharpe ratio (1.0-1.5)
- Moderate drawdown (5-10%)
- Tested on 2+ periods
- Win rate 50-60%
- 20-30 trades total

**Low (50-59%)**:
- Meets basic criteria
- Limited testing (1-2 periods)
- Some inconsistency

**Action**: Assign confidence level to strategy.

### Step 4: Document Execution Guidelines

For each validated strategy, document:

1. **Best Market Conditions**
   - When does this strategy work best?
   - Trending markets? Ranging? Volatile?

2. **Entry Timing**
   - When should user enter?
   - Any filters or conditions?

3. **Exit Timing**
   - How does exit work?
   - Automatic or manual?

4. **Risk Management**
   - Position sizing recommendations
   - Maximum position size (% of portfolio)
   - Stop-loss levels

5. **When to Avoid**
   - Market conditions to avoid
   - Indicators that suggest avoiding

**Action**: Write clear, actionable execution guidelines.

### Step 5: Gather Validation History

Collect:
- **Backtest IDs**: List all backtest IDs used
- **Optimization IDs**: If optimization was run
- **Tested Periods**: List all date ranges tested
- **Consistency Notes**: Describe consistency across periods

**Action**: Compile validation history for traceability.

### Step 6: Add to PORTFOLIO.md

Format entry according to PORTFOLIO.md structure:

```markdown
## [SYMBOL] - [Strategy Type]

**Symbol**: [TICKER]
**Strategy Type**: [type]
**Status**: ✅ Validated
**Confidence Level**: [High/Medium/Low] ([X]%)
**Last Updated**: YYYY-MM-DD

### Parameters
- `[param]`: [value]

### Performance Metrics
- **Sharpe Ratio**: [X.X]
- **Total Return**: [X.X]%
- **Win Rate**: [X.X]%
- **Max Drawdown**: -[X.X]%

### Execution Guidelines
- **Best Market Conditions**: [...]
- **Entry Timing**: [...]
- **Exit Timing**: [...]
- **Risk Management**: [...]
- **When to Avoid**: [...]

### Validation History
- Backtest IDs: `[bt_xxx, bt_yyy]`
- Tested Periods: [...]
- Consistency: [...]

### Notes
- [...]
```

**Action**: Add formatted entry to PORTFOLIO.md.

## Example Curation Session

1. Review CONTEXTS.md
   - Find: "trailing-stop on AAPL tested 3 times, Sharpe ratios: 1.8, 1.7, 1.9"

2. Validate criteria
   - ✅ All criteria met

3. Calculate confidence
   - High (85%): Consistent, high Sharpe, low drawdown

4. Document guidelines
   - Best conditions: Trending markets
   - Entry: On pullback, RSI < 70
   - Risk: Max 5% of portfolio

5. Add to PORTFOLIO.md
   - Format entry with all sections
   - Link to backtest IDs

## Quality Control

Before adding to PORTFOLIO.md, ensure:
- ✅ All entry criteria met
- ✅ Confidence level calculated
- ✅ Execution guidelines complete
- ✅ Validation history documented
- ✅ Entry formatted correctly

## Updating Existing Entries

If new backtest data becomes available:
1. Review new results
2. Update performance metrics if improved
3. Recalculate confidence level if changed
4. Update "Last Updated" date
5. Add new backtest IDs to validation history

## Documentation

After curation:
- Document curation process in CONTEXTS.md
- Note which strategies were added
- Note which strategies were considered but not added (and why)

## Next Steps

After adding to PORTFOLIO.md:
- User can reference PORTFOLIO.md for execution-ready strategies
- Continue backtesting to find more strategies
- Periodically review PORTFOLIO.md entries for updates
