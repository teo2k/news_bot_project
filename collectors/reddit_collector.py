import http.client
import json
from datetime import datetime, timedelta
from urllib.parse import urlparse
import base64
import logging
import yaml
from pathlib import Path
import asyncio
import time

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Пути к конфигурации
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "config.yaml"

def load_config():
    """Загружает конфигурацию из файла config.yaml."""
    try:
        with open(CONFIG_PATH, "r") as f:
            config = yaml.safe_load(f)
        logger.info("Конфигурация успешно загружена")
        return config
    except Exception as e:
        logger.error(f"Ошибка при загрузке конфигурации: {e}")
        raise

class RedditCollector:
    def __init__(self, config):
        self.config = config
        self.client_id = self.config["collectors"]["reddit"]["client_id"]
        self.client_secret = self.config["collectors"]["reddit"]["client_secret"]
        self.user_agent = self.config["collectors"]["reddit"]["user_agent"]
        self.subreddits = self._get_subreddits()
        self.token = None
        self.token_expiry = None
        self.logger = logger
        self.latest_posts = []  # Добавляем список для хранения постов

    def _get_subreddits(self):
        """Получает список сабреддитов из конфигурации."""
        try:
            subreddits = self.config["collectors"]["reddit"]["subreddits"]
            if not isinstance(subreddits, list):
                raise ValueError("subreddits должен быть списком")
            return subreddits
        except KeyError as e:
            self.logger.error(f"Отсутствует ключ в конфигурации: {e}")
            raise
        except ValueError as e:
            self.logger.error(f"Неверный формат subreddits: {e}")
            raise

    async def _get_access_token(self):
        """Получение или обновление OAuth2-токена с использованием http.client."""
        if self.token and self.token_expiry > datetime.now():
            return self.token

        try:
            parsed_url = urlparse("https://www.reddit.com/api/v1/access_token")
            conn = http.client.HTTPSConnection(parsed_url.netloc)

            self.logger.info(f"Запрос токена с client_id: {self.client_id}, user_agent: {self.user_agent}")

            auth_string = f"{self.client_id}:{self.client_secret}"
            auth_encoded = base64.b64encode(auth_string.encode()).decode()

            headers = {
                "User-Agent": self.user_agent,
                "Authorization": f"Basic {auth_encoded}"
            }
            payload = "grant_type=client_credentials"

            conn.request("POST", parsed_url.path, body=payload, headers=headers)
            response = conn.getresponse()

            if response.status == 200:
                data = json.loads(response.read().decode())
                self.token = data["access_token"]
                self.token_expiry = datetime.now() + timedelta(seconds=data["expires_in"])
                self.logger.info("Токен доступа успешно получен")
                return self.token
            else:
                error_text = response.read().decode()
                self.logger.error(f"Не удалось получить токен доступа: {response.status} - {error_text}")
                raise Exception(f"Не удалось получить токен доступа: {response.status} - {error_text}")
        except Exception as e:
            self.logger.error(f"Ошибка при получении токена доступа: {e}")
            raise
        finally:
            conn.close()

    def _fetch_posts(self, subreddit):
        """Синхронный метод для получения постов из субреддита через http.client."""
        try:
            token = asyncio.run(self._get_access_token())  # Получаем токен синхронно
            parsed_url = urlparse(f"https://oauth.reddit.com/r/{subreddit}/new.json?limit=10")
            conn = http.client.HTTPSConnection(parsed_url.netloc)

            headers = {
                "Authorization": f"Bearer {token}",
                "User-Agent": self.user_agent
            }

            conn.request("GET", parsed_url.path + "?" + parsed_url.query, headers=headers)
            response = conn.getresponse()

            if response.status == 200:
                data = json.loads(response.read().decode())
                posts = data["data"]["children"]
                return [post["data"] for post in posts]
            else:
                self.logger.error(f"Не удалось получить посты из r/{subreddit}: {response.status}")
                return []
        except Exception as e:
            self.logger.error(f"Ошибка при получении постов из r/{subreddit}: {e}")
            return []
        finally:
            conn.close()

    async def collect_posts(self):
        """Асинхронный сбор новых постов из указанных сабреддитов с фильтрацией."""
        self.logger.info("Starting Reddit post collection with API...")
        self.logger.debug(f"Collected posts: {self.latest_posts}")
        keywords = self.config["collectors"]["reddit"].get("keywords", ["bitcoin", "ethereum", "crypto", "price"])

        while True:
            for subreddit_name in self.subreddits:
                try:
                    # Выполняем синхронный запрос в отдельном потоке
                    posts = await asyncio.to_thread(self._fetch_posts, subreddit_name)
                    for post in posts:
                        title_lower = post["title"].lower()
                        text_lower = post["selftext"].lower()
                        if any(keyword.lower() in title_lower or keyword.lower() in text_lower for keyword in keywords):
                            post_data = {
                                "batch_time": int(time.time()),
                                "source": "Reddit",
                                "text": post["selftext"],
                                "title": post["title"],
                                "author": post["author"] if post["author"] else "Anonymous",
                                "date": post["created_utc"],
                                "score": post["score"],
                                "source_reliability": self.config["source_reliability"]["reddit"]
                            }
                            self.logger.info(f"Relevant post from r/{subreddit_name}: {post_data['title']}")
                            self.latest_posts.append(post_data)
                except Exception as e:
                    self.logger.error(f"Error collecting from r/{subreddit_name}: {e}")
            await asyncio.sleep(300)  # Ждем 5 минут перед следующим сбором

    def get_latest_posts(self):
        """Возвращает список собранных постов и очищает его."""
        posts = self.latest_posts.copy()
        self.latest_posts.clear()
        return posts

# Пример использования
if __name__ == "__main__":
    config = load_config()
    collector = RedditCollector(config)
    asyncio.run(collector.collect_posts())
