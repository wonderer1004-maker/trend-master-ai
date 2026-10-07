import numpy as np
import pandas as pd


def sma(s, n): return s.rolling(n).mean()
def rsi(close, n=14):
    d=close.diff(); up=d.clip(lower=0); dn=-d.clip(upper=0)
    rs=up.ewm(alpha=1/n,adjust=False).mean()/dn.ewm(alpha=1/n,adjust=False).mean().replace(0,np.nan)
    return 100-(100/(1+rs))
def atr(df,n=20):
    pc=df.Close.shift(1); tr=pd.concat([(df.High-df.Low).abs(),(df.High-pc).abs(),(df.Low-pc).abs()],axis=1).max(axis=1)
    return tr.rolling(n).mean()

def enrich(df):
    d=df.copy()
    for n in (20,50,150,200): d[f'MA{n}']=sma(d.Close,n)
    d['RSI']=rsi(d.Close); d['ATR']=atr(d); d['VOL20']=d.Volume.rolling(20).mean()
    d['VOLR']=d.Volume/d.VOL20.replace(0,np.nan)
    d['H20']=d.High.shift(1).rolling(20).max(); d['H55']=d.High.shift(1).rolling(55).max()
    d['H252']=d.High.shift(1).rolling(252).max(); d['L252']=d.Low.shift(1).rolling(252).min()
    return d

def market_regime(df):
    d=enrich(df).dropna();
    if len(d)<5: return {'score':50,'regime':'SIDEWAYS','exposure':0.4,'risk':0.005}
    x=d.iloc[-1]; score=0
    score += 20 if x.Close>x.MA200 else 0
    score += 15 if x.MA50>x.MA200 else 0
    score += 15 if d.MA200.iloc[-1]>d.MA200.iloc[-20] else 0
    score += 15 if x.Close>x.MA50 else 0
    score += 10 if x.Close>x.MA20 else 0
    score += 10 if x.RSI>=50 else 0
    score += 15 if x.Close>=0.9*x.H252 else 0
    if score>=80: return {'score':score,'regime':'STRONG BULL','exposure':1.0,'risk':0.01}
    if score>=65: return {'score':score,'regime':'BULL','exposure':0.8,'risk':0.0075}
    if score>=45: return {'score':score,'regime':'SIDEWAYS','exposure':0.45,'risk':0.005}
    if score>=25: return {'score':score,'regime':'BEAR','exposure':0.2,'risk':0.0025}
    return {'score':score,'regime':'STRONG BEAR','exposure':0.05,'risk':0.0025}

def master_score(df):
    d=enrich(df).dropna(); x=d.iloc[-1]; score=0; parts={}
    trend=sum([x.Close>x.MA50,x.Close>x.MA150,x.Close>x.MA200,x.MA50>x.MA150,x.MA150>x.MA200])
    parts['trend']=round(15*trend/5,1); score+=parts['trend']
    stage=15 if (x.Close>x.MA150 and d.MA150.iloc[-1]>d.MA150.iloc[-20]) else 0; parts['weinstein']=stage; score+=stage
    near_high= x.Close>=.85*x.H252; off_low=x.Close>=1.25*x.L252
    parts['relative_strength_proxy']=15 if near_high else 7 if x.Close>=.75*x.H252 else 0; score+=parts['relative_strength_proxy']
    breakout=0
    if x.Close>x.H20: breakout+=7
    if x.Close>x.H55: breakout+=5
    if near_high: breakout+=3
    parts['breakout']=breakout; score+=breakout
    vol=10 if x.VOLR>=2 else 7 if x.VOLR>=1.5 else 3 if x.VOLR>=1 else 0; parts['volume']=vol; score+=vol
    mom=10 if 55<=x.RSI<=75 else 6 if 50<=x.RSI<80 else 2; parts['momentum']=mom; score+=mom
    quality=10 if off_low else 4; parts['structure']=quality; score+=quality
    parts['industry_placeholder']=5; score+=5
    return {'score':min(100,round(score,1)),'parts':parts,'rsi':round(float(x.RSI),1),'volume_ratio':round(float(x.VOLR),2),'atr':float(x.ATR),'close':float(x.Close),'breakout20':bool(x.Close>x.H20),'breakout55':bool(x.Close>x.H55)}

def trade_plan(df, account=10_000_000, risk_pct=.01, max_weight=.2):
    s=master_score(df); entry=s['close']; stop=entry-2*s['atr']; unit=max(entry-stop,1e-9)
    qty_risk=int(account*risk_pct/unit); qty_cap=int(account*max_weight/entry)
    qty=max(0,min(qty_risk,qty_cap))
    return {**s,'entry':entry,'stop':stop,'quantity':qty,'position_value':qty*entry,'risk_amount':qty*unit}
