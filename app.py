import requests
import feedparser
import pandas as pd
import streamlit as st
import urllib.parse
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

feedparser.USER_AGENT = "Mozilla/5.0 (compatible; StablecoinNewsApp/1.0)"

# 30초마다 자동 새로고침
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

# ── 5. 화면 구성
st.title("🛡️ 스테이블코인 디페그 모니터")
st.caption(f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

prices = get_prices()

# 히스토리에 현재 가격 추가
st.session_state.price_history.append({
    "시간": datetime.now().strftime("%H:%M:%S"),
    "USDT": prices["USDT"],
    "USDC": prices["USDC"],
    "DAI":  prices["DAI"]
})

# 최근 50개만 유지
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
    df_history = df_history.set_index("시간")
    st.line_chart(df_history)
else:
    st.info("데이터 수집 중... 30초 후 그래프가 나타납니다.")

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