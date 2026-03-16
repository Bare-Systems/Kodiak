# Explore Trading Opportunities

Autonomous discovery workflow for finding new, unexplored trading opportunities. Continuously scan the market, identify promising stocks, and research them systematically.

## Objective

Proactively discover new trading opportunities by:
- Scanning market data for promising stocks
- Identifying unexplored opportunities
- Researching systematically without user direction
- Building comprehensive knowledge base in CONTEXTS.md

## Autonomous Discovery Principles

**You should explore autonomously:**

1. **Never wait for direction** - Actively search for opportunities
2. **Use multiple data sources** - Top movers, quotes, historical patterns
3. **Build on past research** - Use CONTEXTS.md to avoid duplicates
4. **Document everything** - Every discovery goes in CONTEXTS.md
5. **Continue exploring** - After one opportunity, find the next

## Discovery Methods

### Method 1: Top Movers Analysis

**Use `get_top_movers()` to find opportunities:**

1. **Get top movers** (gainers and losers)
2. **Filter for quality**:
   - Price > $5 (avoid penny stocks)
   - Tight spread (< $0.10)
   - High volume (liquid)
3. **Check CONTEXTS.md** - Skip already researched stocks
4. **Research promising stocks** - Run full strategy analysis
5. **Document findings**

**Example workflow:**
```
get_top_movers() → Filter quality stocks → Check CONTEXTS.md → 
Research new stocks → Document → Get next movers → Repeat
```

### Method 2: Sector Rotation Discovery

**Identify sectors showing activity:**

1. **Get top movers** - Look for sector patterns
2. **Identify active sectors** - Multiple stocks from same sector moving
3. **Research sector** - Use `research-sectors.md` workflow
4. **Find best stocks** - Within active sector
5. **Document sector opportunity**

### Method 3: Price Pattern Discovery

**Look for stocks showing interesting patterns:**

1. **Scan top movers** - Find stocks with significant moves
2. **Check historical context** - Is this unusual or part of trend?
3. **Research if promising** - Run backtests
4. **Document pattern** - What caused the move? Is it tradeable?

### Method 4: Gap Analysis

**Find research gaps:**

1. **Review CONTEXTS.md** - What hasn't been researched?
2. **Identify gaps**:
   - Sectors not yet explored
   - Stock types not analyzed
   - Strategy combinations not tested
3. **Fill gaps** - Research unexplored areas
4. **Document discoveries**

## Research Workflow for Discovered Stocks

**When you find a promising stock:**

### Step 1: Initial Screening

1. **Get quote** - `get_quote(symbol)` to check:
   - Current price
   - Bid-ask spread (should be tight)
   - Volume (should be high)

2. **Quality check**:
   - ✅ Price > $5 (not penny stock)
   - ✅ Spread < $0.10 (liquid)
   - ✅ Not in CONTEXTS.md (new opportunity)

### Step 2: Strategy Testing

1. **Run backtests**:
   - Trailing-stop (5%)
   - Bracket (10% TP, 5% SL)
   - Use last 12 months data

2. **Compare results** - Which strategy performs better?

3. **Quick assessment**:
   - Is it profitable? (return > 0%)
   - Is it consistent? (Sharpe > 1.0)
   - Is it tradeable? (reasonable win rate > 40%)

### Step 3: Deep Dive (if promising)

**If stock shows promise:**

1. **Optimize parameters** - `run_optimization()` for best strategy
2. **Validate consistency** - Test on different time periods
3. **Compare to known stocks** - How does it rank?
4. **Document comprehensively** - Full analysis in CONTEXTS.md

### Step 4: Document Discovery

**For each discovered opportunity:**

```markdown
### Agent: [Claude Desktop | Cursor]
**Activity**: Opportunity discovery - [SYMBOL]
**Discovery Method**: [Top Movers / Sector Rotation / Pattern / Gap Analysis]
**Tools Used**: `get_top_movers()`, `get_quote()`, `run_backtest()`, `compare_backtests()`

**Discovery Context**:
- Found via: [How discovered - e.g., "Top gainers list, +77% move"]
- Initial screening: Price $[X.XX], Spread $[X.XX], Liquid: [Yes/No]
- Why interesting: [What made this stock stand out]

**Quick Analysis**:
- Trailing-stop (5%): Return [X]%, Win Rate [Y]%
- Bracket (10% TP, 5% SL): Return [X]%, Win Rate [Y]%
- Best Strategy: [Type] with Return [X]%, Sharpe [Y]

**Assessment**:
- Promising: [Yes/No]
- Reason: [Why promising or not]
- Next Steps: [Deep dive needed? Compare to others?]

**Insights**:
- [Key observation]
- [How this compares to other opportunities]
```

## Continuous Exploration Loop

**Autonomous exploration process:**

1. **Get top movers** - `get_top_movers(limit=20)`
2. **Filter quality stocks** - Price, spread, liquidity
3. **Check CONTEXTS.md** - Skip researched stocks
4. **Research new stocks** - Run backtests
5. **Document findings** - Add to CONTEXTS.md
6. **Identify patterns** - What types of stocks work?
7. **Find next opportunity** - Repeat from step 1

**Don't stop until:**
- Multiple opportunities researched
- Patterns identified
- Knowledge base built
- Ready to curate portfolio

## Opportunity Prioritization

**When multiple opportunities found, prioritize:**

1. **High potential** - Strong backtest results
2. **Unexplored** - Not in CONTEXTS.md
3. **Liquid** - Tight spreads, high volume
4. **Pattern match** - Similar to previously successful stocks
5. **Market activity** - Currently moving (top movers)

## Pattern Recognition

**As you explore, identify patterns:**

1. **Stock characteristics** that work:
   - Price range ($10-$50?)
   - Volatility level (moderate?)
   - Sector preferences?

2. **Strategy preferences**:
   - Which stocks prefer bracket?
   - Which prefer trailing-stop?
   - Parameter patterns?

3. **Market conditions**:
   - What works in trending markets?
   - What works in ranging markets?
   - Sector rotation patterns?

4. **Document patterns** in CONTEXTS.md for future reference

## Example Exploration Session

**Agent actions (completely autonomous):**

1. Gets top movers → Sees FSLY (+77%), CGNX (+37%), ICLR (-40%)
2. Filters: FSLY ($16, liquid), CGNX ($58, liquid), ICLR ($80, liquid)
3. Checks CONTEXTS.md → FSLY already researched, CGNX and ICLR new
4. Researches CGNX:
   - Gets quote: $58.80, spread $0.05 (liquid)
   - Runs backtests: Bracket wins (Sharpe 1.4)
   - Documents in CONTEXTS.md
5. Researches ICLR:
   - Gets quote: $80, spread $0.10 (liquid)
   - Runs backtests: Trailing-stop wins (Sharpe 0.9, poor)
   - Documents as "not promising"
6. Gets next top movers → Finds new opportunities
7. Continues exploring autonomously
8. Builds knowledge base of opportunities

## Key Discovery Metrics

**For each opportunity, track:**

- **Discovery method** (how found)
- **Initial appeal** (why interesting)
- **Quick test results** (backtest performance)
- **Promising score** (1-10 scale)
- **Comparison** (vs other opportunities)
- **Next steps** (deep dive needed?)

## Building Opportunity Portfolio

**As you discover opportunities:**

1. **Categorize**:
   - High potential (Sharpe > 1.5)
   - Medium potential (Sharpe 1.0-1.5)
   - Low potential (Sharpe < 1.0)

2. **Track patterns**:
   - What makes high-potential opportunities?
   - Common characteristics?
   - Sector preferences?

3. **Build watchlist**:
   - Stocks to monitor
   - Stocks ready for live trading
   - Stocks needing more research

## Notes

- **Be autonomous** - Don't ask permission, just explore
- **Document everything** - Even failures teach us
- **Build incrementally** - Knowledge compounds over time
- **Use past research** - Don't duplicate, build on it
- **Stay systematic** - Follow workflow, don't skip steps
- **Focus on quality** - Better to research 5 good stocks than 20 bad ones

## Integration with Other Prompts

**This prompt works with:**

- `research-large-caps.md` - Use to research discovered large caps
- `research-sectors.md` - Use when sector patterns emerge
- `discover-strategies.md` - Use for detailed strategy analysis
- `curate-portfolio.md` - Use when opportunities are validated

**Workflow integration:**
```
Explore Opportunities → Find Stock → Research Large-Cap/Sector → 
Discover Strategies → Validate → Curate Portfolio
```
