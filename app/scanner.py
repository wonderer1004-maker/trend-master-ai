import pandas as pd
import yfinance as yf
import FinanceDataReader as fdr
from core import master_score

def universe(market):
    if market == "KR":
        x=fdr.StockListing("KRX")
        x=x[x["Code"].astype(str).str.match(r"^\d{6}$")].copy()
        x["Symbol"]=x["Code"].astype(str).str.zfill(6)
        x["YF"]=x["Symbol"]+".KS"
        if "Market" in x.columns:
            kosdaq=x["Market"].astype(str).str.contains("KOSDAQ",case=False,na=False)
            x.loc[kosdaq,"YF"]=x.loc[kosdaq,"Symbol"]+".KQ"
        return x[["Symbol","YF","Name"]].drop_duplicates("YF")
    parts=[]
    for m in ("NASDAQ","NYSE","AMEX"):
        try:
            z=fdr.StockListing(m)
            symcol="Symbol" if "Symbol" in z.columns else "Code"
            namecol="Name" if "Name" in z.columns else symcol
            q=z[[symcol,namecol]].copy(); q.columns=["Symbol","Name"]; q["YF"]=q.Symbol
            parts.append(q)
        except Exception:
            pass
    return pd.concat(parts,ignore_index=True).drop_duplicates("YF") if parts else pd.DataFrame(columns=["Symbol","YF","Name"])

def _one(symbol):
    try:
        d=yf.download(symbol,period="2y",auto_adjust=True,progress=False,threads=False)
        if isinstance(d.columns,pd.MultiIndex): d.columns=d.columns.get_level_values(0)
        if len(d)<260: return None
        last=d.iloc[-1]
        if float(last.Close)*float(last.Volume) < 1_000_000: return None
        s=master_score(d)
        return {"Ticker":symbol,"Score":s["score"],"Price":round(s["close"],2),"RSI":s["rsi"],
                "VolRatio":s["volume_ratio"],"20D":s["breakout20"],"55D":s["breakout55"],
                "ATR":round(s["atr"],2)}
    except Exception:
        return None

def scan(market="KR", limit=300, topn=30):
    u=universe(market)
    # V1 cloud safety: scan a liquid/sample-sized rotating universe per run.
    # Full exchange universe can be enabled with a scheduled batch worker in V2.
    if len(u)>limit: u=u.head(limit)
    rows=[]
    for _,r in u.iterrows():
        z=_one(r.YF)
        if z:
            z["Name"]=r.Name; z["Symbol"]=r.Symbol; rows.append(z)
    if not rows: return pd.DataFrame()
    out=pd.DataFrame(rows).sort_values(["Score","VolRatio"],ascending=False)
    out["Signal"]=out.apply(lambda r:"BUY CANDIDATE" if r.Score>=80 and (r["20D"] or r["55D"]) else "READY" if r.Score>=70 else "WATCH",axis=1)
    return out.head(topn).reset_index(drop=True)
