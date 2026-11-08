import argparse
import logging
import sys

from src.config import Config, ConfigError
from src.storage import StorageManager
from src.notifier.telegram import TelegramNotifier
from src.stores.blinkit import BlinkitStore
from src.stores.zepto import ZeptoStore
from src.checker import StockChecker


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Hot Wheels die-cast car stock alerts.")
    parser.add_argument("--health", action="store_true", help="Send a Telegram scan health report.")
    args = parser.parse_args(argv)

    try:
        config = Config()
        config.setup_logging()
        storage = StorageManager(config.alerts_db_path)
        notifier = TelegramNotifier(config.bot_token, config.chat_id)
        stores = [
            BlinkitStore(config.blinkit_location, config.blinkit_search_url),
            ZeptoStore(config.zepto_location, config.zepto_search_url),
        ]
        checker = StockChecker(config, storage, notifier, stores)
        return 0 if checker.run_check(health_mode=args.health) else 1
    except ConfigError as exc:
        logging.basicConfig(level=logging.INFO)
        logging.error("Configuration error: %s", exc)
        return 1
    except Exception:
        logging.basicConfig(level=logging.INFO)
        logging.exception("Fatal stock-check error.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
