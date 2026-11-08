# Hot Wheels Die-cast Car Stock Alerts

A Python project that can monitor configured store search integrations and send Telegram notifications when a Hot Wheels die-cast car is confirmed in stock.

## Important live-integration status

**The uploaded project's previous Blinkit and Zepto endpoints were not verified public APIs.** Blinkit returned HTTP 403 and Zepto previously failed DNS resolution. This corrected version intentionally does not call those old endpoints and does not attempt to imitate mobile clients, bypass access controls, or generate fake stock.

The Blinkit and Zepto adapters remain disabled until you provide a verified, authorized HTTPS search endpoint for each store. Configure `BLINKIT_SEARCH_URL` and `ZEPTO_SEARCH_URL` only when you have an endpoint and request format authorized by the provider. The included generic request shapes are integration scaffolding, not a claim that either retailer supports them.

Without configured endpoints, scans report the store as unavailable and exit with a failure status. This is intentional: an unavailable store must not look like an empty shelf or a successful scan.

## What changed

- Removed all hardcoded simulated products and all automatic simulation fallback.
- Removed the old `grofers.com/v4/search/` endpoint and the previous unverified Zepto endpoint.
- Stock status is `Unknown` unless the response explicitly confirms availability. Only `In Stock` can trigger an alert.
- Watchlist now requires a Hot Wheels brand match and excludes tracks, playsets, keychains, stickers and other accessories.
- Store failures preserve the last known in-stock state and make the run fail visibly.
- Telegram messages use escaped HTML rather than fragile Markdown formatting.
- State writes use atomic replacement.
- Scheduled workflow has one 15-minute schedule; 08:00 IST is already one of those runs. Overlapping jobs are queued rather than cancelled.
- The sample `alerts.json` has been reset because the old history contained demo-product hashes, not verified real-stock events.

## Setup

Python 3.12 or newer is recommended.

```bash
pip install -r requirements.txt
```

Set these environment variables (GitHub Actions repository secrets for hosted runs):

| Variable | Required | Purpose |
|---|---:|---|
| `BOT_TOKEN` | Yes | Telegram bot token |
| `CHAT_ID` | Yes | Telegram destination chat ID |
| `BLINKIT_LOCATION` | No | Your store delivery location value, if required by the authorized API |
| `ZEPTO_LOCATION` | No | Your store delivery location value, if required by the authorized API |
| `BLINKIT_SEARCH_URL` | No | Verified, authorized HTTPS Blinkit search endpoint |
| `ZEPTO_SEARCH_URL` | No | Verified, authorized HTTPS Zepto search endpoint |
| `LOG_LEVEL` | No | Logging level; defaults to `INFO` |

Do not put bot tokens or other credentials in source files or commit them to GitHub. If a real token was ever committed publicly, revoke it and create a replacement.

Create a local `.env` file only on your own computer and keep it out of Git:

```env
BOT_TOKEN=your_token
CHAT_ID=your_chat_id
BLINKIT_LOCATION=your_delivery_location
ZEPTO_LOCATION=your_delivery_location
# Add the *_SEARCH_URL variables only after verifying the provider's authorized API contract.
```

## Run

```bash
python -m src.main
python -m src.main --health
pytest -q
```

A missing/unverified store endpoint is reported as unavailable. Telegram alerts are sent only for products that pass all of these checks:

1. The listing name contains Hot Wheels.
2. It is not an excluded accessory, track or playset.
3. The provider response explicitly confirms `In Stock`.
4. The product has a stable HTTPS product URL.

## GitHub Actions

Add `BOT_TOKEN` and `CHAT_ID` as repository Actions secrets. Add location secrets if required by your authorized integration. Add `BLINKIT_SEARCH_URL` / `ZEPTO_SEARCH_URL` only after confirming the endpoints and request/response formats with the retailer or an authorized provider.

The workflow runs every 15 minutes. The 08:00 IST time is already included in that schedule; there is no duplicate daily cron. A manual run can request a Telegram health report.

## Current limitation

This project correction improves safety, filtering, reliability, error visibility and tests. It does **not** restore live retailer data access by itself. Blinkit/Zepto live monitoring remains pending a verified authorized data source and matching response schema. Do not treat a green CI test run as proof of live retailer connectivity.
