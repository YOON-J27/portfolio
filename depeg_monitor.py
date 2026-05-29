import requests

# CoinGecko API로 USDT, USDC, DAI 가격 가져오기
url = "https://api.coingecko.com/api/v3/simple/price"

params = {
    "ids": "tether,usd-coin,dai",
    "vs_currencies": "usd"
}

response = requests.get(url, params=params)
data = response.json()

# 가격 출력
usdt = data["tether"]["usd"]
usdc = data["usd-coin"]["usd"]
dai  = data["dai"]["usd"]

print(f"USDT: ${usdt}")
print(f"USDC: ${usdc}")
print(f"DAI:  ${dai}")

# 디페그 감지
print("\n--- 디페그 감지 ---")
if usdt < 0.99 or usdt > 1.01:
    print(f"⚠️  USDT 디페그! 현재 가격: ${usdt}")
else:
    print(f"✅ USDT 정상: ${usdt}")

if usdc < 0.99 or usdc > 1.01:
    print(f"⚠️  USDC 디페그! 현재 가격: ${usdc}")
else:
    print(f"✅ USDC 정상: ${usdc}")

if dai < 0.99 or dai > 1.01:
    print(f"⚠️  DAI 디페그! 현재 가격: ${dai}")
else:
    print(f"✅ DAI 정상: ${dai}")