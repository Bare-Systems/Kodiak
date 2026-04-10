# Research Market Sectors

Autonomous research workflow for sector-based equity discovery and strategy development. Systematically explore sectors to identify profitable trading opportunities.

## Objective

Systematically research market sectors to:
- Identify promising sectors and individual stocks within them
- Discover sector-specific trading patterns
- Find optimal strategies for sector characteristics
- Build sector knowledge base in CONTEXTS.md

## Autonomous Research Principles

**You should research proactively:**

1. **Review CONTEXTS.md** - Check what sectors/stocks have been researched
2. **Identify unexplored sectors** - Focus on sectors not yet analyzed
3. **Use sector data** - Leverage `get_top_movers()` to find active sectors
4. **Build sector knowledge** - Document sector-specific patterns
5. **Continue autonomously** - Move through sectors systematically

## Target Sectors

Focus on these major market sectors:

**Technology:**
- Software (CRM, ADBE, NOW, SNOW)
- Semiconductors (NVDA, AMD, INTC, TSM)
- Cloud/Infrastructure (AMZN, MSFT, GOOGL)

**Finance:**
- Banks (JPM, BAC, WFC, C)
- Payment Processors (V, MA, PYPL)
- Insurance (BRK.B, AIG, PRU)

**Healthcare:**
- Pharmaceuticals (JNJ, PFE, MRK, ABBV)
- Biotech (GILD, BIIB, REGN)
- Medical Devices (TMO, DHR, ISRG)

**Consumer:**
- Retail (WMT, TGT, COST, HD)
- E-commerce (AMZN, EBAY, ETSY)
- Consumer Goods (PG, KO, PEP, NKE)

**Energy:**
- Oil & Gas (XOM, CVX, SLB)
- Renewable Energy (ENPH, SEDG, FSLR)

**Industrial:**
- Aerospace (BA, RTX, LMT)
- Manufacturing (CAT, DE, GE)

## Research Workflow

### Step 1: Sector Selection

**Selection strategy:**

1. **Check CONTEXTS.md** - See which sectors are researched
2. **Use top movers** - `get_top_movers()` to identify active sectors
3. **Prioritize unexplored** - Focus on sectors not yet analyzed
4. **Consider market conditions** - Research sectors showing activity

**If using top movers:**
- Look for sector patterns in gainers/losers
- Identify which sectors are moving
- Research stocks within active sectors

### Step 2: Stock Selection Within Sector

**For each sector, select 3-5 representative stocks:**

**Selection criteria:**
1. **Market leaders** - Largest companies in sector
2. **Liquid stocks** - Tight spreads, high volume
3. **Diverse representation** - Different sub-sectors if applicable
4. **Available data** - Stocks with historical data for backtesting

**Example for Technology sector:**
- AAPL (hardware)
- MSFT (software/cloud)
- NVDA (semiconductors)
- GOOGL (advertising/search)

### Step 3: Sector-Wide Analysis

**For each stock in the sector:**

1. **Get current quote** - Check liquidity
2. **Run strategy backtests**:
   - Trailing-stop (5%)
   - Bracket (10% TP, 5% SL)
3. **Use consistent period** - Last 12 months
4. **Compare within sector** - Which stocks perform best?

### Step 4: Sector Pattern Analysis

**After testing all stocks in sector:**

1. **Compare performance**:
   - Which strategies work best for this sector?
   - Are there common optimal parameters?
   - Do stocks in sector show similar patterns?

2. **Identify sector characteristics**:
   - Volatility level (high/medium/low)
   - Trend patterns (trending/ranging/volatile)
   - Best strategy type (trailing-stop vs bracket)
   - Optimal parameters (sector-specific)

3. **Document sector insights** in CONTEXTS.md

### Step 5: Cross-Sector Comparison

**After researching multiple sectors:**

1. **Compare sectors**:
   - Which sectors have best trading opportunities?
   - Sector-specific strategy preferences?
   - Risk/return profiles by sector?

2. **Identify patterns**:
   - Do tech stocks prefer bracket strategies?
   - Do financials work better with trailing stops?
   - Sector volatility correlations?

3. **Document cross-sector insights**

### Step 6: Document Sector Research

**For each sector researched, document in CONTEXTS.md:**

```markdown
### Agent: [Claude Desktop | Cursor]
**Activity**: Sector research - [SECTOR NAME]
**Tools Used**: `get_top_movers()`, `get_quote()`, `run_backtest()`, `compare_backtests()`
**Sector**: [SECTOR NAME]
**Stocks Analyzed**: [SYMBOL1, SYMBOL2, SYMBOL3, ...]

**Sector Characteristics**:
- Volatility: [High/Medium/Low]
- Trend Pattern: [Trending/Ranging/Volatile]
- Average Spread: $[X.XX]
- Liquidity: [Good/Fair/Poor]

**Best Performing Stocks**:
1. [SYMBOL] - [Strategy]: Return [X]%, Sharpe [Y]
2. [SYMBOL] - [Strategy]: Return [X]%, Sharpe [Y]
3. [SYMBOL] - [Strategy]: Return [X]%, Sharpe [Y]

**Sector Strategy Preferences**:
- Best Strategy Type: [bracket/trailing-stop]
- Optimal Parameters: [TP: X%, SL: Y%]
- Average Win Rate: [X]%
- Average Return: [X]%

**Sector-Specific Insights**:
- [Observation 1 about sector behavior]
- [Observation 2 about trading patterns]
- [How this sector compares to others]

**Recommendation**: [Which stocks in this sector are best for trading?]
```

## Continuous Research Loop

**After completing one sector:**

1. ✅ Document sector findings in CONTEXTS.md
2. ✅ Move to next unexplored sector automatically
3. ✅ Use top movers to identify active sectors
4. ✅ Build comprehensive sector knowledge

**Research is complete when:**
- All major sectors analyzed
- Sector patterns documented
- Best stocks per sector identified
- Cross-sector comparisons complete

## Using Top Movers for Sector Discovery

**When `get_top_movers()` shows sector activity:**

1. **Identify sector** from top gainers/losers
2. **Select representative stocks** from that sector
3. **Research those stocks** using standard workflow
4. **Document sector findings**
5. **Compare to other sectors**

**Example:**
- Top movers show tech stocks (NVDA, AMD, INTC) moving
- Research Technology sector stocks
- Document tech sector patterns
- Compare to previously researched sectors

## Sector-Specific Considerations

**Technology Sector:**
- Often high volatility
- May prefer bracket strategies (defined targets)
- Watch for earnings-driven moves

**Financial Sector:**
- Interest rate sensitive
- May prefer trailing stops (trend following)
- Lower volatility typically

**Healthcare Sector:**
- Event-driven (FDA approvals, trials)
- High volatility around events
- May need wider stops

**Energy Sector:**
- Commodity price sensitive
- High volatility
- May prefer bracket strategies

## Example Research Session

**Agent actions (autonomous):**

1. Reads CONTEXTS.md → Sees Technology sector partially researched
2. Gets top movers → Sees tech stocks active (NVDA, AMD up)
3. Selects Technology sector for deep dive
4. Chooses 5 tech stocks: AAPL, MSFT, NVDA, GOOGL, META
5. For each stock:
   - Gets quote
   - Runs backtests (trailing-stop, bracket)
   - Compares results
6. Analyzes sector patterns:
   - Tech stocks prefer bracket strategies
   - Optimal: TP 12%, SL 5%
   - Average Sharpe: 1.3
7. Documents Technology sector findings
8. Moves to Finance sector automatically
9. Repeats process

## Key Metrics to Track Per Sector

- **Sector volatility** (average across stocks)
- **Best strategy type** (trailing-stop vs bracket)
- **Optimal parameters** (sector-specific)
- **Top performers** (best stocks in sector)
- **Sector patterns** (common characteristics)
- **Cross-sector ranking** (how sector compares)

## Notes

- Use sector ETFs as proxies if individual stocks unavailable
- Consider sector rotation patterns (which sectors are hot)
- Document both sector winners and losers (learn from both)
- Build sector knowledge incrementally (don't rush)
- Use top movers to guide sector selection (focus on active sectors)
