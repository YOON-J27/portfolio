import requests
import feedparser
import pandas as pd
import streamlit as st
import urllib.parse
import altair as alt
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

feedparser.USER_AGENT = "Mozilla/5.0 (compatible; StablecoinNewsApp/1.0)"

st_autorefresh(interval=30000, key="autorefresh")

# ── 1. 실시간 가격 가져오기
def get_prices():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": "tether,usd-coin,dai", "vs_currencies": "usd"}
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        return {
            "USDT": data.get("tether", {}).get("usd", 1.0),
            "USDC": data.get("usd-coin", {}).get("usd", 1.0),
            "DAI":  data.get("dai", {}).get("usd", 1.0)
        }
    except Exception:
        return {"USDT": 1.0, "USDC": 1.0, "DAI": 1.0}

# ── 2. 디페그 감지
def check_depeg(prices):
    alerts = []
    for coin, price in prices.items():
        if price < 0.99 or price > 1.01:
            alerts.append(f"⚠️ {coin} 디페그! 현재 가격: ${price}")
    return alerts

# ── 3. 가격 히스토리 세션에 쌓기
if "price_history" not in st.session_state:
    st.session_state.price_history = []

# ── 4. 뉴스 가져오기
@st.cache_data(ttl=900)
def get_news():
    query = "stablecoin OR USDC OR USDT OR Tether OR DAI"
    url = ("https://news.google.com/rss/search?q="
           + urllib.parse.quote(query)
           + "&hl=en-US&gl=US&ceid=US:en")
    feed = feedparser.parse(url)
    items = []
    for e in feed.entries:
        items.append({
            "title": e.get("title", ""),
            "link":  e.get("link", "#"),
            "published": e.get("published", "")[:16],
            "source": e.get("source", {}).get("title", ""),
        })
    return items

# ── 5. DefiLlama 수익률 가져오기
@st.cache_data(ttl=3600)
def get_yields():
    try:
        response = requests.get("https://yields.llama.fi/pools", timeout=10)
        data = response.json()
        pools = []
        for pool in data["data"]:
            symbol = pool.get("symbol", "")
            apy = pool.get("apy")
            tvl = pool.get("tvlUsd")
            project = pool.get("project", "")
            chain = pool.get("chain", "")
            if (any(s in symbol.upper() for s in ["USDT", "USDC", "DAI"])
                    and apy is not None
                    and tvl is not None
                    and apy > 0
                    and tvl > 1_000_000):
                pools.append({
                    "프로토콜": project,
                    "코인": symbol,
                    "체인": chain,
                    "APY (%)": round(apy, 2),
                    "TVL ($)": f"${tvl/1_000_000:.1f}M"
                })
        pools.sort(key=lambda x: x["APY (%)"], reverse=True)
        return pools[:15]
    except Exception:
        return []

# ── 6. 화면 구성
st.title("🛡️ 스테이블코인 디페그 모니터")
st.caption(f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

prices = get_prices()

st.session_state.price_history.append({
    "시간": datetime.now().strftime("%H:%M:%S"),
    "USDT": prices["USDT"],
    "USDC": prices["USDC"],
    "DAI":  prices["DAI"]
})

if len(st.session_state.price_history) > 50:
    st.session_state.price_history = st.session_state.price_history[-50:]

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="USDT", value=f"${prices['USDT']}", delta=round(prices["USDT"] - 1.0, 4))
with col2:
    st.metric(label="USDC", value=f"${prices['USDC']}", delta=round(prices["USDC"] - 1.0, 4))
with col3:
    st.metric(label="DAI",  value=f"${prices['DAI']}",  delta=round(prices["DAI"]  - 1.0, 4))

st.divider()

alerts = check_depeg(prices)
if alerts:
    for alert in alerts:
        st.error(alert)
else:
    st.success("✅ 현재 디페그 없음 — 세 코인 모두 정상입니다")

st.divider()

st.subheader("📈 실시간 가격 추이")
if len(st.session_state.price_history) > 1:
    df_history = pd.DataFrame(st.session_state.price_history)
    df_melt = df_history.melt("시간", var_name="코인", value_name="가격")
    chart = alt.Chart(df_melt).mark_line().encode(
        x="시간:O",
        y=alt.Y("가격:Q", scale=alt.Scale(domain=[0.985, 1.005])),
        color="코인:N"
    ).properties(height=300).interactive()
    st.altair_chart(chart, use_container_width=True)
else:
    st.info("데이터 수집 중... 30초 후 그래프가 나타납니다.")

st.divider()

st.subheader("💰 스테이블코인 수익률 순위 (DefiLlama)")
yields = get_yields()
if yields:
    df_yields = pd.DataFrame(yields)
    st.dataframe(df_yields, use_container_width=True, hide_index=True)
    st.caption("TVL $1M 이상 풀만 표시 · 1시간마다 업데이트")
else:
    st.info("수익률 데이터를 불러오는 중입니다...")

st.divider()

st.subheader("📰 스테이블코인 관련 뉴스")
news_list = get_news()
if news_list:
    for item in news_list[:10]:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"**{item['title']}**")
            st.caption(f"🕐 {item['published']}  |  {item['source']}")
        with col2:
            st.markdown(f"[기사 보기]({item['link']})")
        st.divider()
else:
    st.info("뉴스를 불러오는 중입니다...")

st.divider()

if st.button("🔄 지금 다시 확인"):
    st.cache_data.clear()
    st.rerun()