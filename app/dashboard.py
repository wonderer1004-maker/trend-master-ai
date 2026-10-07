import streamlit as st
import yfinance as yf
import pandas as pd
from core import market_regime, master_score, trade_plan
from backtest import backtest

st.set_page_config(page_title='TREND MASTER ADAPTIVE V1',page_icon='📈',layout='wide')
st.title('📈 TREND MASTER ADAPTIVE V1')
st.caption('Livermore · Weinstein · Turtle · O’Neil · Minervini · Darvas — market-regime adaptive research dashboard')
with st.sidebar:
    symbol=st.text_input('Symbol','NVDA').strip().upper(); benchmark=st.text_input('Market benchmark','SPY').strip().upper()
    years=st.slider('History (years)',2,10,7); account=st.number_input('Account size',100000,1000000000,10000000,100000)
    breakout=st.selectbox('Turtle breakout',[55,20]); run=st.button('Analyze',type='primary',use_container_width=True)
@st.cache_data(ttl=900)
def load(sym,period):
    d=yf.download(sym,period=f'{period}y',auto_adjust=True,progress=False)
    if isinstance(d.columns,pd.MultiIndex): d.columns=d.columns.get_level_values(0)
    return d.dropna()
if run:
    try:
        df=load(symbol,years); bm=load(benchmark,years)
        if len(df)<260 or len(bm)<260: st.error('At least ~260 trading days are required.'); st.stop()
        regime=market_regime(bm); score=master_score(df); plan=trade_plan(df,account,regime['risk']); bt=backtest(df,account,regime['risk'],breakout)
        a,b,c,d=st.columns(4); a.metric('Market regime',regime['regime']); b.metric('Market score',f"{regime['score']}/100"); c.metric('MASTER score',f"{score['score']}/100"); d.metric('Suggested exposure',f"{regime['exposure']:.0%}")
        st.subheader(f'{symbol} price'); st.line_chart(df.Close)
        st.subheader('Signal / risk plan'); st.json({'RSI':score['rsi'],'Volume ratio':score['volume_ratio'],'20D breakout':score['breakout20'],'55D breakout':score['breakout55'],'Entry reference':round(plan['entry'],2),'ATR stop':round(plan['stop'],2),'Position quantity':plan['quantity'],'Risk amount':round(plan['risk_amount'],2)})
        st.subheader('MASTER score components'); st.bar_chart(pd.Series(score['parts']))
        st.subheader('Backtest'); m=bt['metrics']; cols=st.columns(6)
        for col,(k,v) in zip(cols,m.items()): col.metric(k, f'{v:.2%}' if k in ['Total Return','CAGR','MDD','Win Rate'] else f'{v:.2f}' if isinstance(v,(int,float)) else str(v))
        st.line_chart(bt['equity'])
        st.caption('Research/education only. Validate out-of-sample before real-money use. Market/industry/fundamental scoring will be expanded in later versions.')
    except Exception as e: st.error(f'Analysis failed: {e}')
else:
    st.info('Enter a US ticker (NVDA) or Yahoo Finance Korea ticker (005930.KS), then tap Analyze.')
