# Project audit and handover

## User's selected scope

Monitor Hot Wheels die-cast cars only. Do not alert on tracks, playsets, keychains, stickers, display/storage products, or unrelated Hot Wheels merchandise.

## Audit findings in the uploaded November 6 project

1. `src/stores/blinkit.py` called the old `https://grofers.com/v4/search/` endpoint. The user's previous run returned HTTP 403.
2. `src/stores/zepto.py` used an undocumented Zepto API hostname/path. The previous run reported a DNS failure.
3. Both adapters defaulted `SIMULATE_STORES` to `true` and returned hardcoded mock products after failed requests.
4. Both parsers treated missing stock fields as in-stock (`in_stock=True` / `out_of_stock=False` defaults).
5. The watchlist included generic terms such as `Hot Wheels`, `Premium`, `2025`, and `2026`, and only excluded a small number of accessories.
6. The checker logged store failures but did not return a failing process status, so a workflow could look green even when scans failed.
7. The stock workflow had both a 15-minute cron and a separate 08:00 IST cron, even though 08:00 IST is already included in the 15-minute schedule.
8. Telegram messages used Markdown without escaping product-provided text.
9. `alerts.json` contained six hashes that exactly match the hardcoded Blinkit/Zepto mock product URLs. Those entries are demo history, not verified real-stock history.

## Changes in this corrected archive

- Removed all generated/mock product fallbacks and the `SIMULATE_STORES` behavior.
- Removed the old Grofers endpoint and the previous unverified Zepto endpoint.
- Disabled live store requests until a verified, authorized HTTPS endpoint is configured in `BLINKIT_SEARCH_URL` / `ZEPTO_SEARCH_URL`.
- Added official-host validation for configured endpoints and returned product links.
- Changed missing/unknown stock to `Unknown`; only explicit `In Stock` is eligible for a notification.
- A relevant listing with unknown stock, malformed product response, HTTP refusal, or network error marks that store scan incomplete and preserves its previous state.
- Tightened the watchlist to require Hot Wheels branding and exclude non-car merchandise.
- Made checker failures affect the process exit code and included store failures in optional health reports.
- Made state-file writes atomic.
- Switched Telegram notifications to HTML with escaped product text.
- Removed duplicate cron schedule and prevented cancellation of an in-progress scan.
- Reset `alerts.json` because the prior records corresponded to simulated products.
- Added tests for store endpoint configuration, parsing, unknown stock, die-cast filtering, checker failure handling and Telegram escaping.

## Verification performed

- `python -m compileall -q src tests` — passed.
- `pytest -q` — 18 tests passed.
- `config/watchlist.json` and `alerts.json` — valid JSON.
- Searched source for old mock-generation functions, `SIMULATE_STORES`, and the old endpoints — no active code references remain.

## What is not yet solved

The corrected code is not proof of live Blinkit or Zepto access. Neither retailer's public, authorized search API contract was supplied in the project, and the previous integrations failed. This archive intentionally does not try to bypass anti-bot controls or invent replacement endpoints. Live monitoring remains pending a provider-authorized endpoint and its documented request/response schema.

Until then, GitHub Actions will report the stores as unavailable and the scan job will fail visibly rather than sending fake restock alerts. Telegram delivery can still be tested independently, but a successful Telegram test does not prove live stock retrieval.

## Handover after replacing the GitHub repository files

1. Keep `BOT_TOKEN` and `CHAT_ID` only in GitHub Actions Secrets; never commit them.
2. Keep location values in secrets if the eventual authorized provider requires them.
3. Do not set `BLINKIT_SEARCH_URL` or `ZEPTO_SEARCH_URL` to guessed endpoints. Add them only after confirming the provider's authorized endpoint, request method, location format and response schema.
4. Run the CI workflow and confirm all 18 tests pass.
5. Manually run the stock workflow. Until authorized endpoints are configured, expect a clear unavailable-store result and no stock alerts.
6. Once a legitimate provider contract is available, adapt the relevant store parser to that schema and add fixture tests before enabling scheduled monitoring.
