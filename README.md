# TREND MASTER ADAPTIVE V1

Market-regime adaptive trend-following research web app for Korean and US stocks.

## Core ideas
- Market regime: Strong Bull / Bull / Sideways / Bear / Strong Bear / Recovery
- Weinstein Stage 2
- Minervini Trend Template
- Livermore / Darvas breakout
- Turtle 20/55-day breakout
- RSI and volume confirmation
- ATR stop and position sizing
- Backtesting dashboard

## Run locally
```bash
pip install -r requirements.txt
streamlit run app/dashboard.py
```

## Examples
- US: NVDA, AAPL, MSFT
- Korea (Yahoo Finance symbols): 005930.KS, 000660.KS

## Important
This project is for research/education. Signals are not guaranteed investment recommendations. Validate with out-of-sample and walk-forward tests before real-money use.
