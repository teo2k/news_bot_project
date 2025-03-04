import asyncio
from collectors.reddit_collector import RedditCollector
from processor.data_processor import DataProcessor
from collectors.price_collector import PriceCollector
from database.db import CryptoDB
from collectors.block_collector import BlockCollector
import logging
from pathlib import Path
import yaml

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Пути к конфигурации
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "config.yaml"

# Загрузка конфигурации
def load_config():
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


async def merge_data():
    # Загружаем конфигурацию
    config = load_config()

    # Инициализируем базу данных
    db = CryptoDB()
    db.initialize_db()

    # Инициализируем модули
    reddit_collector = RedditCollector(config)
    data_processor = DataProcessor(config)
    price_collector = PriceCollector(config)
    block_collector = BlockCollector(config)
    # Запускаем сбор данных из Reddit в фоновом режиме и сбор данных с сайта TheBlock раз в 3 часа
    asyncio.create_task(block_collector.collect_news_periodically(interval=3 * 3600))
    asyncio.create_task(reddit_collector.collect_posts())
    while True:
        # Получаем свежие посты
        posts = reddit_collector.get_latest_posts()
        for post in posts:
            # Анализируем текст поста
            analysis = data_processor.analyze_text(post["text"])
            coins = analysis["coins"]  # Извлечённые криптовалюты
            sentiment = analysis["sentiment"]
            topic = analysis["topic"]
            # Получаем метрики для каждой упомянутой криптовалюты
            for coin in coins:
                metrics = price_collector.get_coin_metrics(coin)
                coin = [coin] if isinstance(coin, str) else coin
                if metrics:
                    db_data = (
                        post["batch_time"],
                        post["source"],
                        post["text"],
                        post["author"],
                        post["date"],
                        post["score"],
                        coin,
                        metrics["price"],
                        sentiment,
                        topic,
                        metrics["volume_24h"],
                        metrics["market_cap"],
                        metrics["volatility_24h"],
                        post["source_reliability"],
                        metrics["price_24h_ago"],
                        metrics["price_30d_ago"]
                    )
                    logging.debug(f"Data for insert: {db_data}")
                    db.insert_data(db_data)
                    logging.info(f"Сохранена запись для {coin} из поста: {post['title']}")
                else:
                    logging.warning(f"Метрики для {coin} не найдены, пропуск записи")
        news = block_collector.get_latest_news()
        for item in news:
            # Анализируем текст новости
            analysis = data_processor.analyze_text(item["text"])
            coins = analysis["coins"]  # Извлечённые криптовалюты
            sentiment = analysis["sentiment"]
            topic = analysis["topic"]
            # Получаем метрики для каждой упомянутой криптовалюты
            for coin in coins:
                metrics = price_collector.get_coin_metrics(coin)
                coin = [coin] if isinstance(coin, str) else coin
                if metrics:
                    db_data = (
                        item["batch_time"],
                        item["source"],
                        item["text"],
                        "Unknown",
                        item["date"],
                        0,
                        coin,
                        metrics["price"],
                        sentiment,
                        topic,
                        metrics["volume_24h"],
                        metrics["market_cap"],
                        metrics["volatility_24h"],
                        item["source_reliability"],
                        metrics["price_24h_ago"],
                        metrics["price_30d_ago"]
                    )
                    logging.debug(f"Data for insert: {db_data}")
                    db.insert_data(db_data)
                    logging.info(f"Сохранена запись для {coin} из новости: {item['title']}")
                else:
                    logging.warning(f"Метрики для {coin} не найдены, пропуск записи")

        await asyncio.sleep(6)


if __name__ == "__main__":
    asyncio.run(merge_data())
