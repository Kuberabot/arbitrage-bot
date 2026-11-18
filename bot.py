
def fetch_orderbook(pair):
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    urls = [
        f"https://api.coindcx.com/market_data/orderbook?pair={pair}",
        f"https://public.coindcx.com/market_data/orderbook?pair={pair}",
    ]
    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code != 200:
                continue
            data = r.json()
            # 【entity-CoinDCX¦canonical_name=CoinDCX】 sometimes returns {"bids": {...}, "asks": {...}}
            # sometimes returns {"orderbook": {"bids":...}}
            if "orderbook" in data:
                data = data["orderbook"]
            bids = data.get("bids", {})
            asks = data.get("asks", {})
            if not bids or not asks:
                continue
            # bids/asks can be dict {price: qty} or list [[price,qty]]
            if isinstance(bids, list):
                best_bid = max(Decimal(str(x[0])) for x in bids)
            else:
                best_bid = max(Decimal(p) for p in bids.keys())
            if isinstance(asks, list):
                best_ask = min(Decimal(str(x[0])) for x in asks)
            else:
                best_ask = min(Decimal(p) for p in asks.keys())
            return (best_bid, best_ask)
        except Exception:
            continue
    return None
