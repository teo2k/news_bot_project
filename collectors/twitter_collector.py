import logging
from pathlib import Path
import asyncio
import tweepy
import yaml
import json
import time
from typing import List

# Пути к конфигурации
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "config.yaml"

# Загрузка конфигурации
def load_config():
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

# Класс для стриминга твитов (API v2)
class TwitterStreamListener(tweepy.StreamingClient):
    def __init__(self, bearer_token, accounts, **kwargs):
        super().__init__(bearer_token, **kwargs)
        self.accounts = accounts
        self.logger = logging.getLogger(__name__)

    def on_tweet(self, tweet):
        # Проверяем, что твит от одного из отслеживаемых аккаунтов
        if str(tweet.author_id) in self.accounts:
            self.logger.info(f"New tweet from @{tweet.author_id}: {tweet.text}")
            # Здесь можно добавить отправку твита в очередь или базу данных

    def on_error(self, status):
        self.logger.error(f"Error in stream: {status}")

    def on_exception(self, exception):
        self.logger.error(f"Exception in stream: {exception}")

# Основной класс коллектора Twitter
class TwitterCollector:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.accounts = self._get_accounts()
        self.client = self._setup_client_v2()

    def _get_accounts(self):
        """Получение списка аккаунтов из конфигурации."""
        accounts = self.config["collectors"]["twitter"]["accounts"]
        return [account.lstrip("@") for account in accounts]

    def _setup_client_v2(self):
        """Настройка клиента Twitter API v2."""
        bearer_token = self.config["collectors"]["twitter"]["bearer_token"]
        return tweepy.Client(bearer_token=bearer_token)

    def _load_cached_ids(self) -> List[str]:
        """Загрузка кэшированных ID из файла."""
        cache_file = BASE_DIR / "cache" / "twitter_ids.json"
        if cache_file.exists():
            with open(cache_file, "r") as f:
                return json.load(f)
        return []

    def _save_cached_ids(self, account_ids: List[str]):
        """Сохранение ID в файл."""
        cache_file = BASE_DIR / "cache" / "twitter_ids.json"
        cache_file.parent.mkdir(exist_ok=True)
        with open(cache_file, "w") as f:
            json.dump(account_ids, f)

    async def _convert_accounts_to_ids(self) -> List[str]:
        cached_ids = self._load_cached_ids()
        if cached_ids:
            self.logger.info("Using cached account IDs.")
            return cached_ids

        account_ids = []
        client = self._setup_client_v2()
        for name in self.accounts:
            max_retries = 3
            retry_count = 0
            while retry_count < max_retries:
                try:
                    user = client.get_user(username=name)
                    account_ids.append(str(user.data.id))
                    self.logger.info(f"Got ID for @{name}: {user.data.id}")
                    break
                except tweepy.TooManyRequests as e:
                    retry_count += 1
                    wait_time = 2 ** retry_count
                    self.logger.warning(f"Rate limit hit for @{name}. Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                except Exception as e:
                    self.logger.error(f"Failed to get ID for @{name}: {e}")
                    break
            if retry_count == max_retries:
                self.logger.error(f"Max retries reached for @{name}. Skipping...")
            await asyncio.sleep(1)  # Задержка между запросами
        self._save_cached_ids(account_ids)
        return account_ids

    async def start_stream(self):
        """Запуск стриминга твитов через API v2."""
        self.logger.info("Starting Twitter stream...")
        account_ids = await self._convert_accounts_to_ids()
        if not account_ids:
            self.logger.error("No account IDs available, check your access level or API limits.")
            return

        stream = TwitterStreamListener(
            bearer_token=self.config["collectors"]["twitter"]["bearer_token"],
            accounts=account_ids
        )

        # Добавляем правила для отслеживания аккаунтов
        stream.add_rules([tweepy.StreamRule(f"from:{account_id}") for account_id in account_ids])
        await asyncio.to_thread(stream.filter)

# Тестовый запуск
if __name__ == "__main__":
    config = load_config()
    collector = TwitterCollector(config)
    asyncio.run(collector.start_stream())