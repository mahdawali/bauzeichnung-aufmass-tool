# MT5 XAUUSD Scalper Expert Advisor

## Overview

The **MT5 XAUUSD Scalper** is a professional Expert Advisor designed for scalping Gold (XAUUSD) on the 5-minute (M5) timeframe using a Moving Average crossover strategy. The EA implements comprehensive risk management, multiple take-profit levels, and advanced safety features to protect your trading account.

## Table of Contents

1. [Strategy Explanation](#strategy-explanation)
2. [Installation Instructions](#installation-instructions)
3. [Parameter Descriptions](#parameter-descriptions)
4. [Risk Management](#risk-management)
5. [Safety Features](#safety-features)
6. [Backtesting Guidelines](#backtesting-guidelines)
7. [Optimization Tips](#optimization-tips)
8. [Risk Warnings](#risk-warnings)

---

## Strategy Explanation

### Moving Average System

The EA uses three Moving Averages to identify trading opportunities:

1. **Fast MA (Default: 10-period EMA)** - Used for entry signal generation
2. **Medium MA (Default: 20-period EMA)** - Used for trend confirmation
3. **Slow MA (Default: 50-period SMA)** - Used for overall trend direction

### Entry Signals

**BUY Signal:**
- Fast MA crosses **above** Medium MA
- Current price is **above** Slow MA
- All safety conditions are met

**SELL Signal:**
- Fast MA crosses **below** Medium MA
- Current price is **below** Slow MA
- All safety conditions are met

### Exit Strategy

The EA implements a sophisticated multi-level take profit system:

1. **TP1 (150 points)** - Closes 50% of position
2. **TP2 (300 points)** - Closes 30% of position
3. **TP3 (500 points)** - Closes remaining 20%

**Note:** Current implementation uses TP1 as primary take profit. For advanced partial close functionality, consider upgrading to a more sophisticated position management system.

### Trailing Stop

- Activates after price moves 150 points in profit
- Trails the stop loss by 50 points
- Helps lock in profits while allowing trades to run

### Break-Even Protection

- Moves stop loss to entry price after 100 points profit
- Protects against losing trades that initially move in your favor

---

## Installation Instructions

### Step 1: Download the EA

Save the `MT5_XAUUSD_Scalper.mq5` file to your computer.

### Step 2: Copy to MetaTrader 5

1. Open MetaTrader 5
2. Click **File → Open Data Folder**
3. Navigate to `MQL5 → Experts`
4. Copy the `MT5_XAUUSD_Scalper.mq5` file into this folder

### Step 3: Compile the EA

1. In MetaTrader 5, press `F4` to open MetaEditor
2. In the Navigator panel, locate `Experts → MT5_XAUUSD_Scalper.mq5`
3. Double-click to open the file
4. Click the **Compile** button (or press F7)
5. Check for any compilation errors (there should be none)

### Step 4: Attach to Chart

1. Open a XAUUSD chart
2. Set timeframe to **M5** (5 minutes)
3. In Navigator panel, locate `Expert Advisors → MT5_XAUUSD_Scalper`
4. Drag and drop onto the XAUUSD M5 chart
5. In the settings dialog:
   - Enable **Allow Algo Trading**
   - Configure parameters as needed
   - Click **OK**

### Step 5: Enable Automated Trading

Ensure the **Algo Trading** button in the toolbar is enabled (should be green).

---

## Parameter Descriptions

### Moving Average Settings

| Parameter | Default | Description |
|-----------|---------|-------------|
| `FastMA_Period` | 10 | Period for fast moving average (entry signals) |
| `MediumMA_Period` | 20 | Period for medium moving average (confirmation) |
| `SlowMA_Period` | 50 | Period for slow moving average (trend filter) |
| `FastMA_Method` | EMA | Calculation method for fast MA |
| `MediumMA_Method` | EMA | Calculation method for medium MA |
| `SlowMA_Method` | SMA | Calculation method for slow MA |
| `MA_Price` | CLOSE | Price type for MA calculation |

**MA Methods:** SMA (Simple), EMA (Exponential), SMMA (Smoothed), LWMA (Linear Weighted)

### Risk Management

| Parameter | Default | Description |
|-----------|---------|-------------|
| `LotSize` | 0.01 | Fixed lot size for each trade |
| `StopLoss` | 200 | Stop loss in points (200 points = ~$20 for XAUUSD) |
| `TP1_Points` | 150 | First take profit level in points |
| `TP2_Points` | 300 | Second take profit level in points |
| `TP3_Points` | 500 | Third take profit level in points |
| `TP1_Percent` | 50.0 | Percentage to close at TP1 |
| `TP2_Percent` | 30.0 | Percentage to close at TP2 |
| `TP3_Percent` | 20.0 | Percentage to close at TP3 |
| `MaxSpread` | 50 | Maximum spread allowed (in points) |
| `MaxSlippage` | 30 | Maximum slippage tolerance (in points) |
| `BreakEvenPoints` | 100 | Move SL to break-even after this profit |

**Important Notes:**
- For XAUUSD, 1 point = $0.01 per mini lot (0.01 lots)
- 100 points = $1 per mini lot
- Adjust lot size based on your account size and risk tolerance

### Trailing Stop

| Parameter | Default | Description |
|-----------|---------|-------------|
| `UseTrailingStop` | true | Enable/disable trailing stop |
| `TrailingStart` | 150 | Profit level to activate trailing (points) |
| `TrailingStep` | 50 | Distance to trail stop loss (points) |

### Trading Hours Filter

| Parameter | Default | Description |
|-----------|---------|-------------|
| `UseTimeFilter` | true | Enable/disable trading time filter |
| `StartHour` | 8 | Start trading at this hour (server time) |
| `EndHour` | 22 | Stop trading at this hour (server time) |

**Recommended Times:**
- Avoid major news events (NFP, FOMC, etc.)
- Best volatility: London and NY sessions
- Avoid low liquidity periods

### Position Management

| Parameter | Default | Description |
|-----------|---------|-------------|
| `MaxConcurrentTrades` | 1 | Maximum number of open positions |
| `MagicNumber` | 123456 | Unique identifier for EA trades |

### Safety Features

| Parameter | Default | Description |
|-----------|---------|-------------|
| `MinEquity` | 100.0 | Minimum account equity required (USD) |
| `DailyLossLimit` | 50.0 | Maximum daily loss allowed (USD) |
| `MaxDrawdownPercent` | 20.0 | Maximum account drawdown allowed (%) |

---

## Risk Management

### Position Sizing

**Conservative Approach:**
- Use 0.01 lots per $1,000 account balance
- Example: $5,000 account = 0.05 lots

**Moderate Approach:**
- Use 0.01 lots per $500 account balance
- Example: $5,000 account = 0.10 lots

**Aggressive Approach:**
- Use 0.01 lots per $250 account balance
- Example: $5,000 account = 0.20 lots

### Risk Per Trade

With default settings:
- Stop Loss: 200 points = $20 per 0.01 lot
- Risk percentage = (Risk per trade / Account Balance) × 100

**Example Calculations:**

| Account | Lot Size | Risk/Trade | Risk % |
|---------|----------|------------|--------|
| $1,000 | 0.01 | $20 | 2.0% |
| $5,000 | 0.05 | $100 | 2.0% |
| $10,000 | 0.10 | $200 | 2.0% |

### Maximum Drawdown Protection

The EA stops trading if:
- Account drawdown exceeds 20% (default)
- Daily loss exceeds $50 (default)
- Account equity falls below $100 (default)

**Important:** Always adjust these values based on your account size and risk tolerance.

---

## Safety Features

### Pre-Trade Checks

Before opening any position, the EA verifies:

1. ✅ **Account Equity** - Above minimum threshold
2. ✅ **Daily Loss Limit** - Not exceeded
3. ✅ **Maximum Drawdown** - Within acceptable range
4. ✅ **Free Margin** - Sufficient for new position
5. ✅ **Spread** - Below maximum allowed
6. ✅ **Trading Hours** - Within configured time window
7. ✅ **Position Limit** - Max concurrent trades not reached

### Automated Protection

- **Break-Even Stop:** Automatically moves SL to entry after 100 points profit
- **Trailing Stop:** Locks in profits as trade moves favorably
- **Spread Filter:** Prevents trading during high spread conditions
- **Time Filter:** Avoids trading during news events and low liquidity

---

## Backtesting Guidelines

### Historical Data Requirements

1. **Symbol:** XAUUSD (Gold Spot)
2. **Timeframe:** M5 (5 minutes)
3. **Data Quality:** Tick data with real spreads (if available)
4. **Period:** Minimum 3-6 months for initial testing
5. **Testing Mode:** "Every tick based on real ticks" (most accurate)

### Backtesting Steps

1. Open **Strategy Tester** (Ctrl+R)
2. Select `MT5_XAUUSD_Scalper`
3. Configure settings:
   - **Symbol:** XAUUSD
   - **Period:** M5
   - **Date Range:** Last 6-12 months
   - **Execution:** Every tick based on real ticks
   - **Initial Deposit:** Match your real account
4. Set input parameters (use recommended settings below)
5. Click **Start**

### Recommended Test Periods

- **Initial Testing:** 3 months
- **Validation:** 6-12 months
- **Long-term Verification:** 2-3 years
- **Walk-Forward:** 6 months forward test after optimization

### Key Metrics to Analyze

- **Total Net Profit:** Overall profitability
- **Profit Factor:** Gross profit / Gross loss (aim for >1.5)
- **Maximum Drawdown:** Should be <20% of account
- **Win Rate:** Percentage of winning trades (aim for >50%)
- **Risk/Reward Ratio:** Average win / Average loss
- **Sharpe Ratio:** Risk-adjusted returns
- **Recovery Factor:** Net profit / Max drawdown

---

## Optimization Tips

### Parameters to Optimize

**Primary Parameters (High Impact):**
1. FastMA_Period (range: 5-20, step: 1)
2. MediumMA_Period (range: 15-30, step: 1)
3. StopLoss (range: 150-300, step: 25)
4. TP1_Points (range: 100-200, step: 25)

**Secondary Parameters (Moderate Impact):**
1. SlowMA_Period (range: 40-100, step: 10)
2. TrailingStart (range: 100-200, step: 25)
3. TrailingStep (range: 30-70, step: 10)
4. MaxSpread (range: 30-70, step: 10)

**Tertiary Parameters (Fine-tuning):**
1. BreakEvenPoints (range: 50-150, step: 25)
2. StartHour/EndHour (test different sessions)

### Optimization Strategy

1. **Genetic Algorithm**
   - Use for initial parameter discovery
   - Fast but may miss optimal combinations
   - Good for wide parameter ranges

2. **Complete Algorithm**
   - Tests all parameter combinations
   - Slower but more thorough
   - Use for final optimization

3. **Walk-Forward Analysis**
   - Optimize on historical data
   - Test on subsequent out-of-sample data
   - Validates strategy robustness

### Optimization Best Practices

✅ **Do:**
- Optimize on in-sample data (60-70% of data)
- Validate on out-of-sample data (30-40% of data)
- Use realistic spread and commission settings
- Consider multiple metrics (not just profit)
- Test during different market conditions

❌ **Don't:**
- Over-optimize (curve fitting)
- Use all available data for optimization
- Ignore drawdown and risk metrics
- Optimize too many parameters simultaneously
- Trust results without forward testing

### Recommended Parameter Sets

See `config_settings.txt` for pre-configured parameter sets for different risk profiles.

---

## Risk Warnings

### ⚠️ IMPORTANT DISCLAIMER

**Trading foreign exchange, gold, and leveraged products carries a high level of risk and may not be suitable for all investors.**

### Key Risks

1. **Market Risk**
   - Gold (XAUUSD) is highly volatile
   - Large price swings can occur rapidly
   - Past performance does not guarantee future results

2. **Leverage Risk**
   - Leverage can amplify both gains and losses
   - Small price movements can result in significant account changes
   - Always use appropriate position sizing

3. **Technical Risk**
   - EA relies on stable internet connection
   - Server/platform outages can affect trades
   - Always monitor EA performance

4. **Strategy Risk**
   - No strategy wins 100% of the time
   - Market conditions change
   - Regular monitoring and adjustment needed

### Best Practices

✅ **Always:**
- Start with a **demo account** first
- Test thoroughly before live trading
- Use proper risk management (max 2% risk per trade)
- Monitor the EA regularly
- Keep sufficient margin in your account
- Adjust parameters based on market conditions

✅ **Never:**
- Trade with money you can't afford to lose
- Use excessive leverage
- Leave EA running without monitoring
- Ignore safety warnings and error messages
- Trade during major news events without experience

### Recommended Starting Approach

1. **Demo Phase (2-4 weeks)**
   - Test on demo account
   - Verify all functions work correctly
   - Observe trade execution and management

2. **Live Phase 1 (Minimum Lots)**
   - Start with absolute minimum lot size
   - Monitor for 1-2 weeks
   - Verify slippage and spreads are acceptable

3. **Live Phase 2 (Gradual Increase)**
   - Slowly increase lot size if performing well
   - Never increase by more than 50% at a time
   - Continue monitoring closely

---

## Troubleshooting

### Common Issues

**EA Not Trading:**
- Check if "Algo Trading" is enabled
- Verify input parameters are valid
- Check if within trading hours (if time filter enabled)
- Ensure spread is below maximum
- Verify sufficient free margin

**EA Opens Too Many Trades:**
- Check `MaxConcurrentTrades` setting
- Verify Magic Number is unique
- Ensure no conflicting EAs on same symbol

**Trades Not Profitable:**
- Review backtest results
- Consider optimizing parameters
- Check spread and commission costs
- Verify market conditions are suitable

**High Drawdown:**
- Reduce lot size
- Increase stop loss distance
- Reduce maximum concurrent trades
- Enable or adjust safety features

---

## Support and Updates

### Documentation
- Keep this README for reference
- Review all parameters before live trading
- Check logs regularly for warnings/errors

### Best Practices for Live Trading
- **Start Small:** Begin with minimum lot sizes
- **Monitor Daily:** Check positions and equity regularly
- **Backtest First:** Always test on demo before live
- **Stay Informed:** Be aware of major news events
- **Keep Records:** Track performance and adjust as needed

---

## Version History

### Version 1.00
- Initial release
- Moving Average crossover strategy
- Multiple take profit levels
- Trailing stop functionality
- Comprehensive safety features
- Trading time filter
- Risk management controls

---

## Technical Specifications

- **Platform:** MetaTrader 5
- **Language:** MQL5
- **Symbol:** XAUUSD (Gold)
- **Timeframe:** M5 (5 minutes)
- **Strategy:** Moving Average Crossover
- **Execution:** Market Orders
- **Position Management:** Break-even, Trailing Stop

---

## Contact and Disclaimer

This Expert Advisor is provided for educational and informational purposes. The developer assumes no responsibility for any losses incurred through the use of this software. 

**Use at your own risk. Always trade responsibly.**

---

*Last Updated: 2024*
*Version: 1.00*
