import logging
import requests
from datetime import datetime, timedelta
import time
from requests.exceptions import HTTPError

class PriceCollector:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.api_url = "https://api.coingecko.com/api/v3"
        self.coin_list = None  # Кэш для списка монет
        self.last_fetch = None  # Время последнего обновления списка монет
        self.metrics_cache = {}  # Кэш для метрик монет
        self.cache_timeout = 3600  # Тайм-аут кэша в секундах (1 час)

    def _fetch_coin_list(self):
        """Загружает список монет с CoinGecko и обновляет кэш."""
        try:
            response = requests.get(f"{self.api_url}/coins/list", headers={"accept": "application/json"})
            if response.status_code == 200:
                self.coin_list = response.json()
                self.last_fetch = datetime.now()
                self.logger.info("Список монет успешно загружен")
            else:
                self.logger.error(f"Не удалось получить список монет: {response.status_code}")
        except Exception as e:
            self.logger.error(f"Ошибка запроса: {e}")

    def _get_coin_id(self, coin):
        """Находит ID монеты по её имени или символу."""
        if not self.last_fetch or (datetime.now() - self.last_fetch).total_seconds() > self.cache_timeout:
            self._fetch_coin_list()

        if not self.coin_list:
            self.logger.warning("Список монет не загружен")
            return None

        coin_lower = coin.lower()
        for c in self.coin_list:
            if c["name"].lower() == coin_lower or c["symbol"].lower() == coin_lower:
                return c["id"]
        self.logger.warning(f"Монета {coin} не найдена в списке")
        return None

    def _get_historical_price(self, coin_id, days):
        """Получает историческую цену монеты за указанное количество дней назад."""
        date = (datetime.now() - timedelta(days=days)).strftime("%d-%m-%Y")
        try:
            response = requests.get(f"{self.api_url}/coins/{coin_id}/history?date={date}")
            if response.status_code == 200:
                data = response.json()
                return data["market_data"]["current_price"]["usd"] if "market_data" in data else None
            else:
                self.logger.error(f"Ошибка при запросе исторической цены для {coin_id}: {response.status_code}")
                return None
        except Exception as e:
            self.logger.error(f"Ошибка при получении исторической цены: {e}")
            return None

    def get_coin_metrics(self, coin):
        """Получает все метрики для монеты, используя кэш, если данные актуальны."""
        coin_id = self._get_coin_id(coin)
        if not coin_id:
            self.logger.warning(f"ID для {coin} не найден")
            return None

        # Проверяем кэш
        if coin_id in self.metrics_cache:
            cached = self.metrics_cache[coin_id]
            if (datetime.now() - cached["timestamp"]).total_seconds() < self.cache_timeout:
                self.logger.info(f"Используем кэшированные данные для {coin}")
                return cached["metrics"]

        # Если данных нет или они устарели, делаем новый запрос
        retries = 3
        for attempt in range(retries):
            try:
                response = requests.get(f"{self.api_url}/coins/{coin_id}")
                response.raise_for_status()
                data = response.json()
                if 'market_data' not in data:
                    self.logger.error(f"Нет 'market_data' для {coin} (ID: {coin_id})")
                    return None

                # Собираем все метрики
                metrics = {
                    "price": data["market_data"]["current_price"]["usd"],
                    "volume_24h": data["market_data"]["total_volume"]["usd"],
                    "market_cap": data["market_data"]["market_cap"]["usd"],
                    "volatility_24h": data["market_data"]["price_change_percentage_24h"],
                    "price_24h_ago": self._get_historical_price(coin_id, 1),
                    "price_30d_ago": self._get_historical_price(coin_id, 30)
                }

                # Сохраняем в кэш
                self.metrics_cache[coin_id] = {"metrics": metrics, "timestamp": datetime.now()}
                self.logger.info(f"Метрики для {coin} успешно обновлены")
                return metrics

            except HTTPError as e:
                if response.status_code == 429:
                    wait_time = 10 * (2 ** attempt)
                    self.logger.warning(f"Слишком много запросов, ждём {wait_time} секунд...")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"HTTP-ошибка для {coin}: {e}")
                    return None
            except Exception as e:
                self.logger.error(f"Ошибка запроса для {coin}: {e}")
                return None
            finally:
                time.sleep(1.5)  # Задержка между запросами для лимитов API

        self.logger.error(f"Не удалось получить метрики для {coin} после {retries} попыток")
        return None