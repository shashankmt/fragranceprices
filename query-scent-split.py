# scrape_scentsplit.py
import json, re, requests, time, itertools
from urllib.parse import urljoin

BASE = "https://www.scentsplit.com"
YOUR_REFERSION_ID = "kkkk"

def fetch_json_feed():
    page = 1
    while True:
        url = f"{BASE}/products.json?limit=250&page={page}"
        data = requests.get(url, timeout=30).json().get("products", [])
        if not data: break
        for p in data: yield p
        page += 1

def crawl_collection():
    for page in itertools.count(1):
        html = requests.get(f"{BASE}/collections/all?page={page}", timeout=30).text
        slugs = re.findall(r'/products/([\w\-]+)"', html)
        if not slugs: break
        for slug in slugs:
            yield requests.get(f"{BASE}/products/{slug}.json", timeout=20).json()["product"]

try:
    products = list(fetch_json_feed())          # fastest path
except Exception as e:
    print("JSON feed failed, falling back:", e)
    products = list(crawl_collection())         # guaranteed path

rows = []
for p in products:
    brand = p["vendor"].strip()
    frag  = p["title"].replace("Decant", "").strip()
    for v in p["variants"]:
        size_ml = v["grams"] or \
                  float(re.search(r'(\d+(?:\.\d+)?)\s*ml', v["title"], re.I).group(1))
        price   = float(v["price"])
        ppm     = round(price / size_ml, 2)
        rows.append({
            "id":       v["id"],
            "brand":    brand,
            "fragrance":frag,
            "size_ml":  size_ml,
            "price":    price,
            "price_per_ml": ppm,
            "merchant": "Scent Split",
            "aff_url": f"https://www.scentsplit.com/r?{YOUR_REFERSION_ID}"
                       f"&u={BASE}/products/{p['handle']}?variant={v['id']}",
            "last_checked": int(time.time())
        })

with open("docs/decants.json", "w") as f:
    json.dump(rows, f, indent=0)
print(f"Saved {len(rows)} rows")
# print(rows)