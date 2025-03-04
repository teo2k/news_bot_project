import logging
from textblob import TextBlob
import re

class DataProcessor:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        # Список ключевых слов для криптовалют из конфига
        self.crypto_keywords = self.config["processor"]["crypto_keywords"]

    def analyze_text(self, text):
        """Анализирует текст и возвращает данные о криптовалютах, настроении и теме."""
        coins = self._extract_coins(text)
        sentiment = self._analyze_sentiment(text)
        topic = self._detect_topic(text)
        return {
            "coins": coins,
            "sentiment": sentiment,
            "topic": topic
        }

    def _extract_coins(self, text):
        """Извлекает упоминания криптовалют из текста."""
        found_coins = []
        for coin in self.crypto_keywords:
            if re.search(r'\b' + re.escape(coin) + r'\b', text, re.IGNORECASE):
                found_coins.append(coin)
        return found_coins

    def _analyze_sentiment(self, text):
        """Определяет настроение текста."""
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        if polarity > 0.1:
            return "positive"
        elif polarity < -0.1:
            return "negative"
        else:
            return "neutral"

    def _detect_topic(self, text):
        """Определяет тему текста"""
        text_lower = text.lower()
        if "price" in text_lower:
            return "рост цен"
        elif "regulation" in text_lower:
            return "регуляция"
        else:
            return "общая тема"
