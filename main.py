import logging
import logging.config
import yaml
from pathlib import Path
import asyncio
from collectors.twitter_collector import TwitterCollector

# Пути к конфигурациям и логам
BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config" / "config.yaml"
LOGGING_CONFIG_PATH = BASE_DIR / "config" / "logging.yaml"


# Настройка логирования
def setup_logging():
    with open(LOGGING_CONFIG_PATH, "r") as f:
        logging_config = yaml.safe_load(f)
    logging.config.dictConfig(logging_config)


# Загрузка конфигурации
def load_config():
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


async def main():
    # Настройка логирования
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting the news bot project...")

    # Загрузка конфигурации
    config = load_config()
    logger.info("Configuration loaded successfully")

    # Инициализация Twitter-коллектора
    twitter_collector = TwitterCollector(config)
    logger.info("Starting Twitter collector...")

    # Запуск стриминга в отдельной задаче
    asyncio.create_task(twitter_collector.start_stream())

    # Основной цикл
    while True:
        logger.info("Running main loop...")
        await asyncio.sleep(60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Shutting down the bot...")
    except Exception as e:
        logging.getLogger(__name__).error(f"Unexpected error: {e}")