# Pair Scorecard Generator for AlphaGenesis Finals
# Based on 7-day trading history analysis (9,211 log entries)

================================================================================
ALPHAGENESIS FINALS PAIR SCORECARDS
Based on 7-day prelims trading history (9,211 log entries)
================================================================================

Pair              Signals   Orders  Conv%  Exits  Wins Losses  WinRate  AvgMove%  Score
------------------------------------------------------------------------------------------
SOL                   810       20   2.5%     22    20      2    90.9%    1.824%   67.6
LTC                   744       26   3.5%     18    14      4    77.8%    1.042%   54.1
DOGE                  733       20   2.7%     18    14      4    77.8%    0.754%   52.3
ADA                   724       18   2.5%     18    14      4    77.8%    0.899%   53.1
BNB                   723       20   2.8%     18    14      4    77.8%    0.911%   53.2
XRP                   664       16   2.4%     18    14      4    77.8%    0.979%   53.6
BTC                   640       15   2.3%     18    14      4    77.8%    0.727%   52.1
ETH                   571       13   2.3%     18    14      4    77.8%    1.322%   55.6

================================================================================
FINALS PAIR PRIORITY RANKING
================================================================================
  #1 SOL      Score=67.6  WinRate=91%  AvgMove=1.824%  Conversion=2.5%
  #2 ETH      Score=55.6  WinRate=78%  AvgMove=1.322%  Conversion=2.3%
  #3 LTC      Score=54.1  WinRate=78%  AvgMove=1.042%  Conversion=3.5%
  #4 XRP      Score=53.6  WinRate=78%  AvgMove=0.979%  Conversion=2.4%
  #5 BNB      Score=53.2  WinRate=78%  AvgMove=0.911%  Conversion=2.8%
  #6 ADA      Score=53.1  WinRate=78%  AvgMove=0.899%  Conversion=2.5%
  #7 DOGE     Score=52.3  WinRate=78%  AvgMove=0.754%  Conversion=2.7%
  #8 BTC      Score=52.1  WinRate=78%  AvgMove=0.727%  Conversion=2.3%

=== TIER ALLOCATION ===

A (Primary):
  - SOL (score=67.6, WR=91%, avg_move=1.824%)
  - ETH (score=55.6, WR=78%, avg_move=1.322%)
  - LTC (score=54.1, WR=78%, avg_move=1.042%)

B (Secondary):
  - XRP (score=53.6, WR=78%, avg_move=0.979%)
  - BNB (score=53.2, WR=78%, avg_move=0.911%)
  - ADA (score=53.1, WR=78%, avg_move=0.899%)

C (Monitor only):
  - DOGE (score=52.3, WR=78%, avg_move=0.754%)
  - BTC (score=52.1, WR=78%, avg_move=0.727%)

=== PHASE 1 RECOMMENDATION (Days 1-5) ===
Trade ONLY Tier A pairs with 8x leverage, 2% risk per trade
Goal: Build +10-15% cushion with highest-conviction pairs

=== DO-NOT-TRADE-UNLESS GATES ===
ALL pairs: regime must be low_volatility or strong_trend (no ranging/chop)
SOL/DOGE: Require ATR expansion flag (high beta, avoid squeeze chop)
BTC/ETH: Minimum confidence 0.65 (liquid but noisy)
XRP: Watch for news spikes (SEC/regulatory headlines)
LTC/ADA: Only trade if Tier A pairs are not signaling
