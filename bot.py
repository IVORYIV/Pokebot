import os, time, requests, logging
from datetime import datetime
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger(__name__)

# ── Config from environment variables ──────────────────────────────────────
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
ZIP_CODE = os.environ.get("ZIP_CODE", "48030")
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL_MINUTES", "30")) * 60

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
    "Accept-Language": "en-US,en;q=0.9",
}

# ── Products to track ───────────────────────────────────────────────────────
BESTBUY_SKUS = {
    "Pokémon Scarlet & Violet Booster Pack": "6570549",
    "Pokémon Prismatic Evolutions ETB":      "6614900",
    "Pokémon 151 Booster Bundle":            "6548072",
    "Pokémon Elite Trainer Box":             "6570550",
}

BRICKSEEK_SKUS = {
    "Pokémon Booster Pack (DG)":   "681041",
    "Pokémon Booster Bundle (DG)": "681044",
}

# ── Telegram ────────────────────────────────────────────────────────────────
def send_telegram(msg: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        log.info("Telegram sent OK")
    except Exception as e:
        log.error(f"Telegram error: {e}")

# ── Best Buy checker ────────────────────────────────────────────────────────
def check_bestbuy(name: str, sku: str) -> bool:
    url = f"https://www.bestbuy.com/api/tcfb/model.json?paths=%5B%5B%22shop%22%2C%22buttonstate%22%2C%22v5%22%2C%22item%22%2C%22skus%22%2C{sku}%2C%22conditions%22%2C%22NONE%22%2C%22destinationZip%22%2C%22{ZIP_CODE}%22%2C%22storeId%22%2C%22storeId%22%5D%5D&method=get"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        data = r.json()
        # Navigate the Falcor response
        btn = data.get("jsonGraph", {}).get("shop", {}).get("buttonstate", {}).get("v5", {}).get("item", {}).get("skus", {}).get(sku, {})
        status = str(btn).lower()
        in_stock = "add_to_cart" in status or "addtocart" in status
        log.info(f"BB {name}: {'IN STOCK' if in_stock else 'out'}")
        return in_stock
    except Exception as e:
        log.warning(f"BB check failed for {name}: {e}")
        return False

# ── BrickSeek / Dollar General checker ─────────────────────────────────────
def check_brickseek(name: str, upc: str) -> tuple[bool, str]:
    url = f"https://brickseek.com/dollar-general-inventory-checker/?sku={upc}&zip={ZIP_CODE}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")
        # Look for in-stock indicators
        page_text = soup.get_text().lower()
        in_stock = "in stock" in page_text and "out of stock" not in page_text[:500]
        qty_el = soup.find(class_=lambda c: c and "quantity" in c.lower())
        qty = qty_el.get_text(strip=True) if qty_el else ""
        log.info(f"DG {name}: {'IN STOCK' if in_stock else 'out'} {qty}")
        return in_stock, qty
    except Exception as e:
        log.warning(f"BrickSeek check failed for {name}: {e}")
        return False, ""

# ── State tracking (avoid duplicate alerts) ─────────────────────────────────
alerted = set()

def check_all():
    found_any = False

    # Best Buy
    for name, sku in BESTBUY_SKUS.items():
        key = f"bb_{sku}"
        in_stock = check_bestbuy(name, sku)
        if in_stock and key not in alerted:
            msg = (
                f"🔵 <b>BEST BUY RESTOCK ALERT</b>\n\n"
                f"✅ <b>{name}</b> is IN STOCK near ZIP {ZIP_CODE}!\n\n"
                f"🛒 Buy now: https://www.bestbuy.com/site/{sku}.p\n"
                f"⏰ {datetime.now().strftime('%I:%M %p')}"
            )
            send_telegram(msg)
            alerted.add(key)
            found_any = True
        elif not in_stock and key in alerted:
            alerted.discard(key)  # reset so we alert again next restock

    # Dollar General via BrickSeek
    for name, upc in BRICKSEEK_SKUS.items():
        key = f"dg_{upc}"
        in_stock, qty = check_brickseek(name, upc)
        if in_stock and key not in alerted:
            msg = (
                f"🟡 <b>DOLLAR GENERAL RESTOCK ALERT</b>\n\n"
                f"✅ <b>{name}</b> spotted near ZIP {ZIP_CODE}!\n"
                f"{f'Qty: {qty}' if qty else ''}\n\n"
                f"🗺️ Check stores: https://brickseek.com/dollar-general-inventory-checker/?sku={upc}&zip={ZIP_CODE}\n"
                f"⏰ {datetime.now().strftime('%I:%M %p')}"
            )
            send_telegram(msg)
            alerted.add(key)
            found_any = True
        elif not in_stock and key in alerted:
            alerted.discard(key)

    if not found_any:
        log.info(f"No new stock found. Next check in {CHECK_INTERVAL//60} min.")

# ── Main loop ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    log.info(f"🚀 PokéBot started! Watching ZIP {ZIP_CODE} every {CHECK_INTERVAL//60} min.")
    send_telegram(
        f"⚡ <b>PokéBot is running!</b>\n\n"
        f"Watching ZIP {ZIP_CODE} for Pokémon card restocks at:\n"
        f"🟡 Dollar General\n🔵 Best Buy\n\n"
        f"You'll get a message the moment something is in stock. Checking every {CHECK_INTERVAL//60} minutes."
    )
    while True:
        try:
            check_all()
        except Exception as e:
            log.error(f"Unexpected error: {e}")
        time.sleep(CHECK_INTERVAL)
