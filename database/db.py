import psycopg2
import logging
import json
from datetime import datetime
import pytz

class CryptoDB:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.connection = None
        self.cursor = None

    def initialize_db(self):
        try:
            self.connection = psycopg2.connect(
                host="localhost",
                port=5432,
                database="crypto_db",
                user="crypto_usr",
                password="your_password"
            )
            self.cursor = self.connection.cursor()
            self.create_table()
            self.logger.info("Успешно подключено к базе данных crypto_db.")
        except Exception as e:
            self.logger.error(f"Ошибка подключения к базе: {e}")
            raise

    def create_table(self):
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS crypto_datasets (
                    id SERIAL PRIMARY KEY,
                    batch_time TIMESTAMP WITH TIME ZONE,
                    date TIMESTAMP WITH TIME ZONE,
                    source TEXT,
                    text TEXT,
                    author TEXT,
                    coin TEXT,
                    price FLOAT,
                    sentiment TEXT,
                    topic TEXT,
                    engagement INTEGER,
                    volume_24h FLOAT,
                    market_cap FLOAT,
                    volatility_24h FLOAT,
                    source_reliability INTEGER,
                    price_24h_ago FLOAT,
                    price_30d_ago FLOAT
                )
            """)
            self.logger.info("Таблица создана или уже существует.")
        except Exception as e:
            self.logger.error(f"Ошибка при создании таблицы: {e}")
            raise

    def check_if_post_exists(self, post_id):
        """Проверяет, существует ли запись для данного поста по его ID."""
        try:
            self.cursor.execute("SELECT EXISTS(SELECT 1 FROM crypto_datasets WHERE post_id = %s)", (post_id,))
            return self.cursor.fetchone()[0]
        except Exception as e:
            self.logger.error(f"Ошибка проверки существования поста {post_id}: {e}")
            return False

    def insert_data(self, data):
        """Вставляет данные в таблицу crypto_datasets."""
        try:
            self.logger.debug(f"Inserting data: {data}")
            processed_data = list(data)

            # Преобразуем временные метки, если они в формате timestamp
            if isinstance(processed_data[0], (int, float)):
                processed_data[0] = datetime.fromtimestamp(processed_data[0], tz=pytz.UTC)
            if isinstance(processed_data[4], (int, float)):
                processed_data[4] = datetime.fromtimestamp(processed_data[4], tz=pytz.UTC)

            # Преобразуем price в JSON, если это словарь
            if isinstance(processed_data[7], dict):
                processed_data[7] = json.dumps(processed_data[7])

            query = """
                INSERT INTO crypto_datasets (
                    batch_time, source, text, author, date, engagement, coin, price, sentiment,
                    topic, volume_24h, market_cap, volatility_24h, source_reliability,
                    price_24h_ago, price_30d_ago
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            self.cursor.execute(query, tuple(processed_data))
            self.connection.commit()
            self.logger.info("Данные успешно добавлены.")
        except Exception as e:
            self.logger.error(f"Ошибка при вставке данных: {e}", exc_info=True)
            raise
