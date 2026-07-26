# Hot Wheels Stock Alerts

A production-ready, modular, and highly extensible Python stock monitor that tracks **Blinkit** and **Zepto** stores for newly available Hot Wheels castings. Whenever a casting matching your watchlist comes back in stock, it immediately alerts you via Telegram.

---

## Features

- 🏪 **Hyperlocal Store Tracking**: Monitors stock updates in real-time for Blinkit and Zepto using coordinate-based lookup settings.
- ⚙️ **Configurable Watchlist**: Manage collectible castings (e.g. `Treasure Hunt`, `Skyline`, `Supra`, `Porsche`) via a simple JSON configuration.
- 🚨 **Anti-Duplicate Engine**: Incorporates a persistent state file (`alerts.json`) that suppresses notifications for items that stay continuously in stock, while instantly alerting you if they sell out and reappear.
- 💬 **Rich Markdown Alerts**: Delivers clean, descriptive Telegram notifications matching your custom format, with timestamps automatically converted to India Standard Time (IST).
- 🧩 **Extensible Architecture**: Built on a solid Interface pattern (`BaseStore`), making it trivial to add new store providers (like Hamleys, Amazon, FirstCry) by writing a single subclass.
- 🔄 **Production-grade CI/CD**: Packages a pre-configured GitHub Actions workflow that runs every 15 minutes and uses secure caches to persist state across runs.

---

## Repository Structure

```text
hotwheels-stock-alerts/
├── .github/
│   └── workflows/
│       └── stock-check.yml   # Scheduled GitHub Actions cron job
├── config/
│   └── watchlist.json        # User defined Hot Wheels watchlist keywords
├── src/
│   ├── notifier/
│   │   ├── __init__.py
│   │   └── telegram.py        # Telegram Bot integration
│   ├── stores/
│   │   ├── __init__.py
│   │   ├── base.py            # BaseStore adapter contract
│   │   ├── blinkit.py         # Blinkit crawler implementation
│   │   └── zepto.py           # Zepto crawler implementation
│   ├── __init__.py
│   ├── checker.py             # Main stock checking pipeline orchestration
│   ├── config.py              # Application configuration and validation
│   ├── filters.py             # Watchlist normalizer and matching logic
│   ├── models.py              # Standardized product dataclass
│   ├── storage.py             # Local state and duplicate prevention
│   └── main.py                # Command-line entry point
├── tests/                     # Comprehensive pytest test suite
│   ├── __init__.py
│   ├── test_checker.py
│   ├── test_filters.py
│   └── test_storage.py
├── .gitignore
├── README.md                  # Setup and execution guide
└── requirements.txt           # Python application dependencies
```

---

## Configuration

The application is configured using environment variables. You can specify these in your OS environment or create a `.env` file in the root folder of the project.

| Variable Name | Required | Description | Example |
| :--- | :--- | :--- | :--- |
| `BOT_TOKEN` | **Yes** | Telegram Bot API token obtained from @BotFather | `718290:AAFdH...` |
| `CHAT_ID` | **Yes** | Your Telegram Chat ID or Channel/Group Chat ID | `987654321` or `-10012345678` |
| `BLINKIT_LOCATION` | **Yes** | Latitude and longitude pair of your delivery address | `12.9716,77.5946` |
| `ZEPTO_LOCATION` | **Yes** | Latitude and longitude pair of your delivery address | `12.9716,77.5946` |
| `LOG_LEVEL` | No | Python logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO` (Default) |
| `SIMULATE_STORES` | No | Toggles simulation mode to generate mock results for testing | `true` (Default) / `false` |

---

## Setup Instructions

### 1. Telegram Bot Setup
1. Open Telegram and search for the official [@BotFather](https://t.me/BotFather).
2. Send `/newbot` and follow the instructions to choose a name and username.
3. Save the **HTTP API Token** provided (this is your `BOT_TOKEN`).

### 2. Getting Your Chat ID
- **To get your private user chat ID:**
  1. Message [@userinfobot](https://t.me/userinfobot) or [@raw_data_bot](https://t.me/raw_data_bot) on Telegram.
  2. It will reply with your unique numerical Chat ID (this is your `CHAT_ID`).
- **To get a Channel/Group Chat ID:**
  1. Add your bot to the group or channel as an Administrator.
  2. Send a dummy message to the channel.
  3. Open your browser and navigate to:
     `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
  4. Search the JSON response for the `"chat"` object. The `"id"` starting with a negative sign (e.g. `-100xxxxxxxxx`) is your `CHAT_ID`.

---

## Running Locally

1. **Prerequisites**: Ensure you have Python 3.12+ installed.
2. **Clone and Navigate**:
   ```bash
   git clone https://github.com/yourusername/hotwheels-stock-alerts.git
   cd hotwheels-stock-alerts
   ```
3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Create Environment Configuration**:
   Create a `.env` file in the root directory:
   ```env
   BOT_TOKEN=your_telegram_bot_token_here
   CHAT_ID=your_telegram_chat_id_here
   BLINKIT_LOCATION=12.9716,77.5946
   ZEPTO_LOCATION=12.9716,77.5946
   LOG_LEVEL=INFO
   SIMULATE_STORES=true
   ```
   > [!NOTE]
   > Keep `SIMULATE_STORES=true` initially to run a mock pass and verify that your Telegram bot works. Once confirmed, set it to `false` to attempt real store API connections.
5. **Run the Application**:
   ```bash
   python src/main.py
   ```
6. **Run Unit Tests**:
   ```bash
   pytest
   ```

---

## Running on GitHub Actions

This repository includes a scheduled workflow that automates execution. It runs every 15 minutes, fetching current stock data and sending alerts.

### Setting Up Secrets
Navigate to your repository page on GitHub:
1. Go to **Settings** > **Secrets and variables** > **Actions**.
2. Click **New repository secret** and add the following:
   - `BOT_TOKEN`
   - `CHAT_ID`
   - `BLINKIT_LOCATION`
   - `ZEPTO_LOCATION`

### How Caching Works (DevOps Architecture)
To satisfy the duplicate notification requirement without writing back to Git (which creates thousands of automated commits), the workflow utilizes `actions/cache`:
1. It looks for a cache matching `stock-alerts-`.
2. If found, it restores `alerts.json` containing previous runs' active in-stock listings and notification logs.
3. The checker runs, updates states, and saves the updated state back to a new cache key.
4. If a casting goes out of stock in Blinkit, the checker notes the absence, and on the next run, it will trigger a new alert if the casting is restocked.

---

## Future Extensibility: Adding a New Store

The project is designed under the Open-Closed Principle. To add a new store (e.g., `FirstCry` or `Hamleys`):

1. **Create a store adapter**: Create a new file in `src/stores/` (e.g. `src/stores/firstcry.py`) inheriting from `BaseStore`:
   ```python
   from src.stores.base import BaseStore
   from src.models import Product
   from typing import List

   class FirstCryStore(BaseStore):
       def __init__(self, location: str):
           self.location = location

       @property
       def name(self) -> str:
           return "FirstCry"

       def search(self, query: str) -> List[Product]:
           # 1. Fetch from FirstCry API
           # 2. Parse products into List[Product]
           # 3. Return the list
           pass
   ```
2. **Register the Store**: Instantiate it in `src/main.py`:
   ```python
   # Import your adapter
   from src.stores.firstcry import FirstCryStore
   
   # Instantiate and append to stores list in main():
   stores = [
       BlinkitStore(config.blinkit_location),
       ZeptoStore(config.zepto_location),
       FirstCryStore(config.firstcry_location)  # Added here!
   ]
   ```
3. No other modules (e.g., matching filters, notification builders, coordinator loops, or state storage managers) need to change!

---

## Troubleshooting

- **Telegram Message Parsing Failures**: Ensure you don't have unescaped Markdown syntax in configuration names. The notifier uses standard Telegram `Markdown` format.
- **Geofenced API blocks**: Blinkit and Zepto do not expose public APIs. If you see warnings like `Network error or anti-bot block on Blinkit` when `SIMULATE_STORES=false`, the store's Web Application Firewall (WAF) or location checker is blocking the requests. Ensure you use coordinates matching real dark stores in your city, and consider using rotating residential proxies or configuring cookies in your headers if you plan to scrape continuously.
- **State reset**: Delete `alerts.json` to purge all notified history and restart checking state.
