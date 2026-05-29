import requests
import pandas as pd
import streamlit as st
from datetime import datetime

# ── 1. 실시간 가격 가져오기
def get_prices():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "tether,usd-coin,dai",
        "vs_currencies": "usd"
    }
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

# ── 3. 30일 과거 데이터
@st.cache_data(ttl=3600)
def get_history(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": 30}
    response = requests.get(url, params=params)
    data = response.json()
    prices = data["prices"]
    df = pd.DataFrame(prices, columns=["timestamp", coin_id])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df = df.set_index("timestamp")
    return df

# ── 4. 뉴스 가져오기
@st.cache_data(ttl=1800)
def get_news():
    import xml.etree.ElementTree as ET
    url = "https://cointelegraph.com/rss/tag/stablecoins"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    if response.status_code != 200:
        return []
    root = ET.fromstring(response.content)
    articles = []
    for item in root.findall(".//item")[:8]:
        title = item.findtext("title", "")
        link  = item.findtext("link", "#")
        date  = item.findtext("pubDate", "")[:16]
        articles.append({"title": title, "url": link, "published_at": date})
    return articles

# ── 5. 화면 구성
st.title("🛡️ 스테이블코인 디페그 모니터")
st.caption(f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

prices = get_prices()

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

st.subheader("📈 30일 가격 추이")
df_usdt = get_history("tether")
df_usdc = get_history("usd-coin")
df_dai  = get_history("dai")
df_all  = pd.concat([df_usdt, df_usdc, df_dai], axis=1, sort=False)
df_all.columns = ["USDT", "USDC", "DAI"]
st.line_chart(df_all)

st.divider()

st.subheader("📰 스테이블코인 관련 뉴스")
news_list = get_news()
if news_list:
    for article in news_list[:8]:
        with st.container():
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**{article.get('title', '제목 없음')}**")
                st.caption(f"🕐 {article.get('published_at', '')[:10]}")
            with col2:
                url = article.get('url', '#')
                st.markdown(f"[기사 보기]({url})")
            st.divider()
else:
    st.info("뉴스를 불러오는 중입니다...")

st.divider()

if st.button("🔄 지금 다시 확인"):
    st.rerun()