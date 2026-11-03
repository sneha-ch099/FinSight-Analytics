import numpy as np
import pandas as pd
import yfinance as yf

TRADING_DAYS=252

def download_prices(tickers_by_name,start_date,end_date):
    series=[];failed=[]
    for name,ticker in tickers_by_name.items():
        try:
            data=yf.download(ticker,start=start_date,end=end_date,interval='1d',auto_adjust=True,progress=False,threads=False,timeout=20)
            if data is None or data.empty or 'Close' not in data.columns:failed.append(name);continue
            close=data['Close']
            if isinstance(close,pd.DataFrame):close=close.iloc[:,0]
            series.append(pd.to_numeric(close,errors='coerce').rename(name))
        except Exception:failed.append(name)
    if not series:raise RuntimeError('No historical prices were returned. Check internet access and ticker symbols.')
    prices=pd.concat(series,axis=1).sort_index();prices=prices[~prices.index.duplicated(keep='last')].dropna(how='all')
    if len(prices)<2:raise RuntimeError('Not enough trading-day observations. Select a longer date range.')
    if failed:print('Data unavailable for:',', '.join(failed))
    return prices

def fetch_latest_quotes(tickers_by_name):
    """Fetch latest available daily quote snapshots; not a guaranteed real-time feed."""
    quotes={}
    for name,ticker in tickers_by_name.items():
        try:
            hist=yf.Ticker(ticker).history(period='5d',interval='1d',auto_adjust=True,timeout=15)
            if hist is None or hist.empty or 'Close' not in hist.columns:quotes[name]={'price':None,'change_pct':None,'time':'unavailable'};continue
            c=hist['Close'].dropna()
            if c.empty:quotes[name]={'price':None,'change_pct':None,'time':'unavailable'};continue
            change=(float(c.iloc[-1])/float(c.iloc[-2])-1)*100 if len(c)>1 and float(c.iloc[-2]) else None
            quotes[name]={'price':float(c.iloc[-1]),'change_pct':change,'time':c.index[-1].strftime('%d %b')}
        except Exception:quotes[name]={'price':None,'change_pct':None,'time':'unavailable'}
    return quotes

def daily_returns(prices):return prices.pct_change(fill_method=None)
def normalize_prices(prices):
    out=prices.copy()
    for col in out.columns:
        valid=out[col].dropna()
        if not valid.empty and valid.iloc[0]!=0:out[col]=out[col]/valid.iloc[0]*100
    return out
def moving_average(prices,window=20):return prices.rolling(window=window,min_periods=1).mean()
def calculate_metrics(prices,risk_free_rate=0.065):
    rows=[]
    for stock in prices.columns:
        s=prices[stock].dropna();r=s.pct_change(fill_method=None).dropna()
        if len(s)<2:continue
        first,last=float(s.iloc[0]),float(s.iloc[-1]);cum=last/first-1 if first else np.nan;n=len(r)
        ann=(last/first)**(TRADING_DAYS/n)-1 if n and first>0 and last>0 else np.nan
        vol=float(r.std(ddof=1)*np.sqrt(TRADING_DAYS)) if len(r)>1 else np.nan
        sharpe=(ann-risk_free_rate)/vol if pd.notna(ann) and pd.notna(vol) and vol>0 else np.nan
        rows.append({'Stock':stock,'First Close':first,'Last Close':last,'Cumulative Return':cum,'Annualized Return':ann,'Annualized Volatility':vol,'Sharpe Ratio':sharpe,'Trading Observations':len(s)})
    if not rows:raise RuntimeError('Not enough valid observations to calculate metrics.')
    return pd.DataFrame(rows).set_index('Stock')
def build_insights(metrics):
    lines=[];r=metrics['Cumulative Return'].dropna();v=metrics['Annualized Volatility'].dropna();sh=metrics['Sharpe Ratio'].dropna()
    if len(r):lines += [f"✦ Strongest cumulative performance: {r.idxmax()} ({r.max():+.2%}).",f"✦ Weakest cumulative performance: {r.idxmin()} ({r.min():+.2%})."]
    if len(v):lines += [f"✦ Highest historical volatility: {v.idxmax()} ({v.max():.2%}).",f"✦ Lowest historical volatility: {v.idxmin()} ({v.min():.2%})."]
    if len(sh):lines += [f"✦ Best Sharpe ratio: {sh.idxmax()} ({sh.max():.2f})."]
    lines += ['', 'HOW TO INTERPRET', '• Higher return means stronger price performance over this period.', '• Higher volatility means larger historical price swings.', '• Sharpe compares excess return with volatility and depends on the risk-free rate.', '', 'Historical performance does not predict future returns. Online quote snapshots may be delayed.']
    return '\n'.join(lines)
