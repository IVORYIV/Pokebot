# ⚡ PokéBot — Pokémon Card Restock Alerter

Checks Dollar General (via BrickSeek) and Best Buy every 30 minutes and sends you a Telegram message the moment Pokémon cards are in stock near your ZIP code.

---

## Setup (takes about 10 minutes)

### Step 1 — Create your Telegram bot (2 min)
1. Open Telegram and search for **@BotFather**
2. Send it: `/newbot`
3. Give it a name like `PokeRestockBot`
4. BotFather gives you a **token** that looks like: `123456789:ABCdef...` — save this
5. Now search for **@userinfobot** in Telegram and send it `/start`
6. It will reply with your **Chat ID** (a number) — save this too

### Step 2 — Deploy to Railway (free, 5 min)
1. Go to **railway.app** and sign up (free — no credit card needed)
2. Click **New Project → Deploy from GitHub**
   - OR click **New Project → Empty Project**, then drag this whole folder in
3. Once deployed, click your service → **Variables** tab
4. Add these environment variables:

| Variable | Value |
|---|---|
| `TELEGRAM_TOKEN` | The token from BotFather |
| `TELEGRAM_CHAT_ID` | Your Chat ID from @userinfobot |
| `ZIP_CODE` | Your ZIP code, e.g. `48030` |
| `CHECK_INTERVAL_MINUTES` | `30` (or less, e.g. `15`) |

5. Click **Deploy** — your bot starts immediately!

### Step 3 — Confirm it's working
You'll get a Telegram message: **"⚡ PokéBot is running!"**

That's it. The bot runs 24/7 and texts you the moment it finds stock.

---

## What it watches
- **Best Buy**: Scarlet & Violet packs, Prismatic Evolutions ETB, 151 Bundle, Elite Trainer Box
- **Dollar General**: Booster packs and bundles (via BrickSeek)

## Customizing
- Edit `BESTBUY_SKUS` in `bot.py` to add/remove Best Buy products (SKU is the number in the Best Buy URL)
- Edit `BRICKSEEK_SKUS` to add DG products (UPC from BrickSeek URL)
- Change `CHECK_INTERVAL_MINUTES` env var to check more/less often

## Cost
Railway free tier gives you $5/month of compute credit — this bot uses ~$0.50/month. Effectively free forever.
