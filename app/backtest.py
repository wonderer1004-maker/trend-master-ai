import numpy as np
import pandas as pd
from .core import enrich

def backtest(df, cash=10_000_000, risk_pct=.01, breakout=55, fee=.00015, slippage=.0005):
    d=enrich(df).dropna().copy(); money=float(cash); qty=0; stop=np.nan; trades=[]; equity=[]; entry=None
    h='H55' if breakout==55 else 'H20'
    for i in range(1,len(d)):
        prev=d.iloc[i-1]; x=d.iloc[i]
        if qty==0:
            signal=(prev.Close>prev[h] and prev.Close>prev.MA50 and prev.MA50>prev.MA150 and 50<=prev.RSI<=80)
            if signal:
                px=x.Open*(1+slippage); st=px-2*prev.ATR; risk=max(px-st,1e-9)
                q=min(int(money*risk_pct/risk),int(money*.2/px))
                cost=q*px*(1+fee)
                if q>0 and cost<=money: money-=cost; qty=q; entry=px; stop=st
        else:
            stop=max(stop, x.Close-3*x.ATR) if pd.notna(x.ATR) else stop
            exit_signal=x.Low<=stop or x.Close<x.MA50
            if exit_signal:
                px=(stop if x.Low<=stop else x.Close)*(1-slippage); proceeds=qty*px*(1-fee)
                pnl=proceeds-qty*entry; money+=proceeds; trades.append(pnl); qty=0; entry=None
        equity.append(money + qty*x.Close)
    if qty:
        px=d.iloc[-1].Close*(1-slippage); proceeds=qty*px*(1-fee); trades.append(proceeds-qty*entry); money+=proceeds; qty=0
        if equity: equity[-1]=money
    eq=pd.Series(equity,index=d.index[1:]); ret=eq.pct_change().dropna(); years=max(len(eq)/252,1/252)
    total=eq.iloc[-1]/cash-1 if len(eq) else 0; cagr=(eq.iloc[-1]/cash)**(1/years)-1 if len(eq) else 0
    dd=eq/eq.cummax()-1 if len(eq) else pd.Series(dtype=float); mdd=dd.min() if len(dd) else 0
    wins=[x for x in trades if x>0]; losses=[x for x in trades if x<=0]
    pf=sum(wins)/abs(sum(losses)) if losses and sum(losses)!=0 else np.inf if wins else 0
    sharpe=np.sqrt(252)*ret.mean()/ret.std() if len(ret)>2 and ret.std()>0 else 0
    downside=ret[ret<0].std(); sortino=np.sqrt(252)*ret.mean()/downside if pd.notna(downside) and downside>0 else 0
    return {'equity':eq,'drawdown':dd,'trades':trades,'metrics':{'Total Return':total,'CAGR':cagr,'MDD':mdd,'Win Rate':len(wins)/len(trades) if trades else 0,'Profit Factor':pf,'Sharpe':sharpe,'Sortino':sortino,'Trades':len(trades)}}
