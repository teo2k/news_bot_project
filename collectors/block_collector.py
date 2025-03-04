import asyncio
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import pytz
import time
import logging

logger = logging.getLogger(__name__)


class BlockCollector:
    def __init__(self, config):
        self.config = config
        self.driver = webdriver.Safari()
        self.latest_news = []

    async def collect_news_periodically(self, interval):
        """Периодически собирает новости с заданным интервалом."""
        while True:
            self.collect_news()
            await asyncio.sleep(interval)

    def collect_news(self):
        """Собирает свежие новости с сайта The Block."""
        driver = self.driver
        url = self.config["collectors"]["block_collector"]["url"]
        driver.get(url)
        time.sleep(5)  # Ожидание полной загрузки страницы

        try:
            # Ожидание загрузки элементов новостей
            news_articles = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "article"))
            )

            for article in news_articles:
                try:
                    # Извлечение заголовка по пути селектора
                    title = article.find_element(By.CSS_SELECTOR, "div.articleCard__text > a > h2 > span").text
                    # Извлечение строки с датой и дополнительной информацией
                    date_str_full = article.find_element(By.CSS_SELECTOR, "div.meta.articleCard__meta > div").text

                    # Извлечение только части с датой (до "•")
                    date_str = date_str_full.split("•")[0].strip()

                    # Преобразование даты в timestamp
                    date_timestamp = self._parse_date(date_str)

                    # Формирование данных новости
                    news_item = {
                        "batch_time": int(time.time()),
                        "source": "The Block",
                        "text": title,
                        "date": date_timestamp,
                        "title": title,
                        "source_reliability": self.config.get("source_reliability", {}).get("the_block", 0.8)
                    }
                    self.latest_news.append(news_item)
                    logger.info(f"Собрана новость: {title}")

                except Exception as e:
                    logger.error(f"Ошибка при обработке новости: {e}")

        except Exception as e:
            logger.error(f"Ошибка при сборе новостей: {e}")

    def _parse_date(self, date_str):
        """Преобразует строку даты в timestamp (Unix time)."""
        try:
            # Формат даты: "Mar 04, 2025, 9:00AM EST"
            date_format = "%b %d, %Y, %I:%M%p %Z"
            # Парсим дату с учетом часового пояса
            date_obj = datetime.strptime(date_str, date_format)
            # Локализуем дату в EST и переводим в UTC
            est = pytz.timezone("US/Eastern")  # EST — Eastern Standard Time
            date_obj = est.localize(date_obj)
            utc_date_obj = date_obj.astimezone(pytz.UTC)
            return int(utc_date_obj.timestamp())
        except ValueError as e:
            logger.error(f"Ошибка преобразования даты '{date_str}': {e}")
            return int(time.time())  # Возвращаем текущее время в случае ошибки

    def get_latest_news(self):
        """Возвращает собранные новости и очищает список."""
        news = self.latest_news.copy()
        self.latest_news.clear()
        return news

    def close(self):
        """Закрывает браузер."""
        self.driver.quit()
