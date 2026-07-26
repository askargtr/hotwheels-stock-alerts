import sys
import argparse
import logging
from src.config import Config, ConfigError
from src.storage import StorageManager
from src.notifier.telegram import TelegramNotifier
from src.stores.blinkit import BlinkitStore
from src.stores.zepto import ZeptoStore
from src.checker import StockChecker

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Hot Wheels Stock Alert system.")
    parser.add_argument(
        "--health",
        action="store_true",
        help="Send a health report message after scanning stores."
    )
    args = parser.parse_args(argv)

    try:
        # Load and validate configurations from env/dotenv
        config = Config()
        config.setup_logging()
    except ConfigError as e:
        # Configuration issues: print to stderr, setup basic logging, and exit
        logging.basicConfig(level=logging.INFO)
        logging.error(f"Configuration initialization failed: {e}")
        return 1
    except Exception as e:
        logging.basicConfig(level=logging.INFO)
        logging.error(f"Failed to start application: {e}")
        return 1

    logger = logging.getLogger("main")
    logger.info("Initializing Hot Wheels Stock Alert checker...")

    try:
        # Instantiate dependencies
        storage = StorageManager(config.alerts_db_path)
        notifier = TelegramNotifier(config.bot_token, config.chat_id)
        
        # Instantiate store adapters
        stores = [
            BlinkitStore(config.blinkit_location),
            ZeptoStore(config.zepto_location)
        ]
        
        # Initialize and run checker orchestrator
        checker = StockChecker(config, storage, notifier, stores)
        checker.run_check(health_mode=args.health)
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error during stock check execution: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
