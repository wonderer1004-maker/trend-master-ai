import streamlit as st
import yfinance as yf
import pandas as pd
from core import market_regime, master_score, trade_plan
from backtest import backtest
from scanner import scan

st.set_page_config(page_title="TREND MASTER ADAPTIVE V1",page_icon="📈",layout="wide")
st.title("📈 TREND MASTER ADAPTIVE V1")
st.caption("시장 국면 자동판정 + 한국/미국 종목 자동 스캔 + MASTER SCORE + 돌파/ATR 위험관리")
tab1,tab2=st.tabs(["🌎 자동 종목 추천","🔎 개별 종목 분석"])

with tab1:
    c1,c2,c3=st.columns(3)
    market=c1.selectbox("시장",["KR","US"],format_func=lambda x:"🇰🇷 국내 KRX" if x=="KR" else "🇺🇸 미국 NASDAQ/NYSE/AMEX")
    scan_count=c2.selectbox("1회 분석 종목 수",[100,200,300,500],index=2)
    topn=c3.selectbox("표시 종목 수",[10,20,30,50],index=2)
    st.info("점수만으로 매수하지 않습니다. BUY CANDIDATE는 MASTER≥80 + 20/55일 돌파 조건을 만족한 연구용 후보입니다.")
    if st.button("🚀 상장주식 자동 분석",type="primary",use_container_width=True):
        with st.spinner("상장 종목을 불러와 가격·추세·RSI·거래량·돌파 조건을 분석 중입니다..."):
            try:
                out=scan(market,scan_count,topn)
                if out.empty: st.warning("이번 스캔에서 조건을 계산할 종목을 찾지 못했습니다.")
                else:
                    st.subheader("🏆 TREND MASTER 추천 후보 순위")
                    st.dataframe(out[["Signal","Score","Symbol","Name","Price","RSI","VolRatio","20D","55D","ATR"]],use_container_width=True,hide_index=True)
                    st.download_button("CSV 다운로드",out.to_csv(index=False).encode("utf-8-sig"),f"trend_master_{market}.csv","text/csv")
            except Exception as e: st.error(f"Scanner failed: {e}")

with tab2:
    with st.sidebar:
        symbol=st.text_input("Symbol","NVDA").strip().upper()
        benchmark=st.text_input("Market benchmark","SPY").strip().upper()
        years=st.slider("History (years)",2,10,7)
        account=st.number_input("Account size",100000,1000000000,10000000,100000)
        breakout=st.selectbox("Turtle breakout",[55,20])
    @st.cache_data(ttl=900)
    def load(sym,period):
        d=yf.download(sym,period=f"{period}y",auto_adjust=True,progress=False)
        if isinstance(d.columns,pd.MultiIndex): d.columns=d.columns.get_level_values(0)
        return d.dropna()
    if st.button("개별 종목 분석",use_container_width=True):
        try:
            df=load(symbol,years); bm=load(benchmark,years)
            if len(df)<260 or len(bm)<260: st.error("최소 약 260 거래일 데이터가 필요합니다."); st.stop()
            regime=market_regime(bm); score=master_score(df); plan=trade_plan(df,account,regime["risk"]); bt=backtest(df,account,regime["risk"],breakout)
            a,b,c,d=st.columns(4); a.metric("Market",regime["regime"]); b.metric("Market score",f'{regime["score"]}/100'); c.metric("MASTER",f'{score["score"]}/100'); d.metric("Exposure",f'{regime["exposure"]:.0%}')
            st.line_chart(df.Close)
            st.json({"RSI":score["rsi"],"Volume ratio":score["volume_ratio"],"20D":score["breakout20"],"55D":score["breakout55"],"Entry":round(plan["entry"],2),"ATR stop":round(plan["stop"],2),"Quantity":plan["quantity"]})
            st.subheader("Backtest"); st.line_chart(bt["equity"]); st.write(bt["metrics"])
        except Exception as e: st.error(f"Analysis failed: {e}")
st.caption("연구·교육용 도구입니다. 자동매매 주문 기능은 포함하지 않습니다.")
