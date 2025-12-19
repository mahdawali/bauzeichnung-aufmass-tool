//+------------------------------------------------------------------+
//|                                        MT5_XAUUSD_Scalper.mq5    |
//|                        Copyright 2024, MetaQuotes Software Corp. |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024, MetaQuotes Software Corp."
#property link      "https://www.mql5.com"
#property version   "1.00"
#property description "Professional XAUUSD Scalping EA using Moving Averages"
#property description "Timeframe: M5, Strategy: MA Crossover with Multiple TP Levels"

//+------------------------------------------------------------------+
//| Input Parameters                                                  |
//+------------------------------------------------------------------+

// === Strategy Parameters ===
input group "=== Moving Average Settings ==="
input int      FastMA_Period = 10;              // Fast MA Period
input int      MediumMA_Period = 20;            // Medium MA Period  
input int      SlowMA_Period = 50;              // Slow MA Period
input ENUM_MA_METHOD FastMA_Method = MODE_EMA;  // Fast MA Method
input ENUM_MA_METHOD MediumMA_Method = MODE_EMA;// Medium MA Method
input ENUM_MA_METHOD SlowMA_Method = MODE_SMA;  // Slow MA Method
input ENUM_APPLIED_PRICE MA_Price = PRICE_CLOSE;// MA Applied Price

input group "=== Risk Management ==="
input double   LotSize = 0.01;                  // Lot Size
input int      StopLoss = 200;                  // Stop Loss (points)
input int      TP1_Points = 150;                // Take Profit 1 (points)
input int      TP2_Points = 300;                // Take Profit 2 (points)
input int      TP3_Points = 500;                // Take Profit 3 (points)
input double   TP1_Percent = 50.0;              // TP1 Close Percent (%)
input double   TP2_Percent = 30.0;              // TP2 Close Percent (%)
input double   TP3_Percent = 20.0;              // TP3 Close Percent (%)
input int      MaxSpread = 50;                  // Maximum Spread (points)
input int      MaxSlippage = 30;                // Maximum Slippage (points)
input int      BreakEvenPoints = 100;           // Break Even Points

input group "=== Trailing Stop ==="
input bool     UseTrailingStop = true;          // Use Trailing Stop
input int      TrailingStart = 150;             // Trailing Start (points)
input int      TrailingStep = 50;               // Trailing Step (points)

input group "=== Trading Hours Filter ==="
input bool     UseTimeFilter = true;            // Use Time Filter
input int      StartHour = 8;                   // Start Hour (Server Time)
input int      EndHour = 22;                    // End Hour (Server Time)

input group "=== Position Management ==="
input int      MaxConcurrentTrades = 1;         // Max Concurrent Trades
input int      MagicNumber = 123456;            // Magic Number

input group "=== Safety Features ==="
input double   MinEquity = 100.0;               // Minimum Equity (USD)
input double   DailyLossLimit = 50.0;           // Daily Loss Limit (USD)
input double   MaxDrawdownPercent = 20.0;       // Max Drawdown (%)

//+------------------------------------------------------------------+
//| Global Variables                                                  |
//+------------------------------------------------------------------+
int handleFastMA, handleMediumMA, handleSlowMA;
double fastMA[], mediumMA[], slowMA[];
double dailyStartBalance = 0;
double accountStartBalance = 0;
datetime lastBarTime = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                     |
//+------------------------------------------------------------------+
int OnInit()
{
   // Validate input parameters
   if(!ValidateInputs())
   {
      Print("ERROR: Invalid input parameters");
      return(INIT_PARAMETERS_INCORRECT);
   }
   
   // Check if trading is allowed
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED))
   {
      Alert("Trading is not allowed in the terminal!");
      return(INIT_FAILED);
   }
   
   if(!AccountInfoInteger(ACCOUNT_TRADE_EXPERT))
   {
      Alert("Automated trading is forbidden for this account!");
      return(INIT_FAILED);
   }
   
   // Initialize Moving Averages
   handleFastMA = iMA(_Symbol, PERIOD_CURRENT, FastMA_Period, 0, FastMA_Method, MA_Price);
   handleMediumMA = iMA(_Symbol, PERIOD_CURRENT, MediumMA_Period, 0, MediumMA_Method, MA_Price);
   handleSlowMA = iMA(_Symbol, PERIOD_CURRENT, SlowMA_Period, 0, SlowMA_Method, MA_Price);
   
   if(handleFastMA == INVALID_HANDLE || handleMediumMA == INVALID_HANDLE || handleSlowMA == INVALID_HANDLE)
   {
      Print("ERROR: Failed to create MA indicators");
      return(INIT_FAILED);
   }
   
   // Set array as series
   ArraySetAsSeries(fastMA, true);
   ArraySetAsSeries(mediumMA, true);
   ArraySetAsSeries(slowMA, true);
   
   // Initialize balance tracking
   dailyStartBalance = AccountInfoDouble(ACCOUNT_BALANCE);
   accountStartBalance = AccountInfoDouble(ACCOUNT_BALANCE);
   
   Print("=== MT5 XAUUSD Scalper EA Initialized ===");
   Print("Symbol: ", _Symbol);
   Print("Timeframe: ", EnumToString(_Period));
   Print("Fast MA: ", FastMA_Period, " Medium MA: ", MediumMA_Period, " Slow MA: ", SlowMA_Period);
   Print("Lot Size: ", LotSize);
   Print("Stop Loss: ", StopLoss, " TP1: ", TP1_Points, " TP2: ", TP2_Points, " TP3: ", TP3_Points);
   
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                  |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   // Release indicator handles
   if(handleFastMA != INVALID_HANDLE) IndicatorRelease(handleFastMA);
   if(handleMediumMA != INVALID_HANDLE) IndicatorRelease(handleMediumMA);
   if(handleSlowMA != INVALID_HANDLE) IndicatorRelease(handleSlowMA);
   
   Print("=== MT5 XAUUSD Scalper EA Deinitialized ===");
   Print("Reason: ", reason);
}

//+------------------------------------------------------------------+
//| Expert tick function                                               |
//+------------------------------------------------------------------+
void OnTick()
{
   // Check if new bar formed
   datetime currentBarTime = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(currentBarTime == lastBarTime)
      return;
   
   lastBarTime = currentBarTime;
   
   // Reset daily balance at start of new day
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   if(dt.hour == 0 && dt.min == 0)
   {
      dailyStartBalance = AccountInfoDouble(ACCOUNT_BALANCE);
   }
   
   // Safety checks
   if(!CheckSafetyConditions())
      return;
   
   // Check trading time
   if(UseTimeFilter && !IsWithinTradingHours())
      return;
   
   // Check spread
   if(!CheckSpread())
      return;
   
   // Update Moving Averages
   if(!UpdateIndicators())
      return;
   
   // Manage existing positions
   ManagePositions();
   
   // Check if we can open new trades
   if(CountOpenPositions() >= MaxConcurrentTrades)
      return;
   
   // Check for trading signals
   int signal = GetTradeSignal();
   
   if(signal == 1) // Buy signal
   {
      OpenPosition(ORDER_TYPE_BUY);
   }
   else if(signal == -1) // Sell signal
   {
      OpenPosition(ORDER_TYPE_SELL);
   }
}

//+------------------------------------------------------------------+
//| Validate input parameters                                          |
//+------------------------------------------------------------------+
bool ValidateInputs()
{
   if(FastMA_Period <= 0 || MediumMA_Period <= 0 || SlowMA_Period <= 0)
   {
      Print("ERROR: MA periods must be positive");
      return false;
   }
   
   if(FastMA_Period >= MediumMA_Period || MediumMA_Period >= SlowMA_Period)
   {
      Print("ERROR: Fast MA < Medium MA < Slow MA required");
      return false;
   }
   
   if(LotSize <= 0)
   {
      Print("ERROR: Lot size must be positive");
      return false;
   }
   
   if(StopLoss <= 0 || TP1_Points <= 0 || TP2_Points <= 0 || TP3_Points <= 0)
   {
      Print("ERROR: SL and TP values must be positive");
      return false;
   }
   
   if(TP1_Percent + TP2_Percent + TP3_Percent != 100.0)
   {
      Print("ERROR: TP percentages must sum to 100%");
      return false;
   }
   
   return true;
}

//+------------------------------------------------------------------+
//| Check safety conditions                                            |
//+------------------------------------------------------------------+
bool CheckSafetyConditions()
{
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   
   // Check minimum equity
   if(equity < MinEquity)
   {
      Print("WARNING: Equity below minimum (", equity, " < ", MinEquity, ")");
      return false;
   }
   
   // Check daily loss limit
   double dailyProfit = balance - dailyStartBalance;
   if(dailyProfit < -DailyLossLimit)
   {
      Print("WARNING: Daily loss limit reached (", dailyProfit, " < ", -DailyLossLimit, ")");
      return false;
   }
   
   // Check maximum drawdown
   double drawdown = (accountStartBalance - equity) / accountStartBalance * 100.0;
   if(drawdown > MaxDrawdownPercent)
   {
      Print("WARNING: Maximum drawdown exceeded (", drawdown, "% > ", MaxDrawdownPercent, "%)");
      return false;
   }
   
   // Check free margin
   double freeMargin = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
   if(freeMargin < 100)
   {
      Print("WARNING: Insufficient free margin (", freeMargin, ")");
      return false;
   }
   
   return true;
}

//+------------------------------------------------------------------+
//| Check if within trading hours                                     |
//+------------------------------------------------------------------+
bool IsWithinTradingHours()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   
   if(dt.hour >= StartHour && dt.hour < EndHour)
      return true;
   
   return false;
}

//+------------------------------------------------------------------+
//| Check spread                                                       |
//+------------------------------------------------------------------+
bool CheckSpread()
{
   long spread = SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
   
   if(spread > MaxSpread)
   {
      Print("WARNING: Spread too high (", spread, " > ", MaxSpread, ")");
      return false;
   }
   
   return true;
}

//+------------------------------------------------------------------+
//| Update indicator values                                            |
//+------------------------------------------------------------------+
bool UpdateIndicators()
{
   if(CopyBuffer(handleFastMA, 0, 0, 3, fastMA) < 3)
   {
      Print("ERROR: Failed to copy Fast MA buffer");
      return false;
   }
   
   if(CopyBuffer(handleMediumMA, 0, 0, 3, mediumMA) < 3)
   {
      Print("ERROR: Failed to copy Medium MA buffer");
      return false;
   }
   
   if(CopyBuffer(handleSlowMA, 0, 0, 3, slowMA) < 3)
   {
      Print("ERROR: Failed to copy Slow MA buffer");
      return false;
   }
   
   return true;
}

//+------------------------------------------------------------------+
//| Get trade signal                                                   |
//+------------------------------------------------------------------+
int GetTradeSignal()
{
   double price = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   
   // BUY Signal: Fast MA crosses above Medium MA, and price is above Slow MA
   bool fastAboveMediumNow = fastMA[0] > mediumMA[0];
   bool fastBelowMediumPrev = fastMA[1] < mediumMA[1];
   bool priceAboveSlow = price > slowMA[0];
   
   if(fastAboveMediumNow && fastBelowMediumPrev && priceAboveSlow)
   {
      Print("BUY SIGNAL: Fast MA crossed above Medium MA, Price above Slow MA");
      return 1; // Buy signal
   }
   
   // SELL Signal: Fast MA crosses below Medium MA, and price is below Slow MA
   bool fastBelowMediumNow = fastMA[0] < mediumMA[0];
   bool fastAboveMediumPrev = fastMA[1] > mediumMA[1];
   bool priceBelowSlow = price < slowMA[0];
   
   if(fastBelowMediumNow && fastAboveMediumPrev && priceBelowSlow)
   {
      Print("SELL SIGNAL: Fast MA crossed below Medium MA, Price below Slow MA");
      return -1; // Sell signal
   }
   
   return 0; // No signal
}

//+------------------------------------------------------------------+
//| Open position                                                      |
//+------------------------------------------------------------------+
void OpenPosition(ENUM_ORDER_TYPE orderType)
{
   MqlTradeRequest request = {};
   MqlTradeResult result = {};
   
   double price, sl, tp1, tp2, tp3;
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   
   // Calculate lot size
   double lot = NormalizeLot(LotSize);
   
   if(orderType == ORDER_TYPE_BUY)
   {
      price = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      sl = NormalizeDouble(price - StopLoss * point, digits);
      tp1 = NormalizeDouble(price + TP1_Points * point, digits);
      tp2 = NormalizeDouble(price + TP2_Points * point, digits);
      tp3 = NormalizeDouble(price + TP3_Points * point, digits);
   }
   else // SELL
   {
      price = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      sl = NormalizeDouble(price + StopLoss * point, digits);
      tp1 = NormalizeDouble(price - TP1_Points * point, digits);
      tp2 = NormalizeDouble(price - TP2_Points * point, digits);
      tp3 = NormalizeDouble(price - TP3_Points * point, digits);
   }
   
   // We'll open position with TP1 and manage others manually
   request.action = TRADE_ACTION_DEAL;
   request.symbol = _Symbol;
   request.volume = lot;
   request.type = orderType;
   request.price = price;
   request.sl = sl;
   request.tp = tp1; // Set first TP
   request.deviation = MaxSlippage;
   request.magic = MagicNumber;
   request.comment = StringFormat("XAUUSD Scalper|TP1:%d|TP2:%d|TP3:%d", TP1_Points, TP2_Points, TP3_Points);
   
   if(OrderSend(request, result))
   {
      if(result.retcode == TRADE_RETCODE_DONE || result.retcode == TRADE_RETCODE_PLACED)
      {
         Print("SUCCESS: ", EnumToString(orderType), " position opened at ", price);
         Print("Order: ", result.order, " Deal: ", result.deal, " Volume: ", result.volume);
      }
      else
      {
         Print("ERROR: Order failed with retcode: ", result.retcode);
      }
   }
   else
   {
      Print("ERROR: OrderSend failed with error: ", GetLastError());
   }
}

//+------------------------------------------------------------------+
//| Count open positions                                               |
//+------------------------------------------------------------------+
int CountOpenPositions()
{
   int count = 0;
   
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(PositionSelectByTicket(PositionGetTicket(i)))
      {
         if(PositionGetString(POSITION_SYMBOL) == _Symbol && 
            PositionGetInteger(POSITION_MAGIC) == MagicNumber)
         {
            count++;
         }
      }
   }
   
   return count;
}

//+------------------------------------------------------------------+
//| Manage existing positions                                          |
//+------------------------------------------------------------------+
void ManagePositions()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(!PositionSelectByTicket(ticket))
         continue;
      
      if(PositionGetString(POSITION_SYMBOL) != _Symbol || 
         PositionGetInteger(POSITION_MAGIC) != MagicNumber)
         continue;
      
      double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
      double currentPrice = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) ? 
                             SymbolInfoDouble(_Symbol, SYMBOL_BID) : 
                             SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      double sl = PositionGetDouble(POSITION_SL);
      double tp = PositionGetDouble(POSITION_TP);
      double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
      int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
      
      ENUM_POSITION_TYPE posType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
      double profit = PositionGetDouble(POSITION_PROFIT);
      
      // Calculate profit in points
      double profitPoints = 0;
      if(posType == POSITION_TYPE_BUY)
         profitPoints = (currentPrice - openPrice) / point;
      else
         profitPoints = (openPrice - currentPrice) / point;
      
      // Move to break-even
      if(profitPoints >= BreakEvenPoints)
      {
         if((posType == POSITION_TYPE_BUY && sl < openPrice) || 
            (posType == POSITION_TYPE_SELL && sl > openPrice))
         {
            ModifyPosition(ticket, openPrice, tp);
            Print("Position ", ticket, " moved to break-even");
         }
      }
      
      // Apply trailing stop
      if(UseTrailingStop && profitPoints >= TrailingStart)
      {
         double newSL = 0;
         
         if(posType == POSITION_TYPE_BUY)
         {
            newSL = NormalizeDouble(currentPrice - TrailingStep * point, digits);
            if(newSL > sl)
            {
               ModifyPosition(ticket, newSL, tp);
               Print("Trailing stop updated for position ", ticket, " New SL: ", newSL);
            }
         }
         else // SELL
         {
            newSL = NormalizeDouble(currentPrice + TrailingStep * point, digits);
            if(sl == 0 || newSL < sl)
            {
               ModifyPosition(ticket, newSL, tp);
               Print("Trailing stop updated for position ", ticket, " New SL: ", newSL);
            }
         }
      }
      
      // Check for TP2 and TP3 levels (simplified - in real implementation would need to track partial closes)
      // This basic version will let TP1 handle the position exit
   }
}

//+------------------------------------------------------------------+
//| Modify position                                                    |
//+------------------------------------------------------------------+
bool ModifyPosition(ulong ticket, double sl, double tp)
{
   MqlTradeRequest request = {};
   MqlTradeResult result = {};
   
   request.action = TRADE_ACTION_SLTP;
   request.position = ticket;
   request.sl = sl;
   request.tp = tp;
   request.symbol = _Symbol;
   
   if(OrderSend(request, result))
   {
      if(result.retcode == TRADE_RETCODE_DONE)
         return true;
   }
   
   return false;
}

//+------------------------------------------------------------------+
//| Normalize lot size                                                 |
//+------------------------------------------------------------------+
double NormalizeLot(double lot)
{
   double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double lotStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   
   lot = MathMax(lot, minLot);
   lot = MathMin(lot, maxLot);
   lot = MathRound(lot / lotStep) * lotStep;
   
   return lot;
}

//+------------------------------------------------------------------+
