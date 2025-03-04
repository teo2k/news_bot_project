# CryptoNewsAnalysis Bot

Краткое описание: CryptoNewsAnalysis Bot — это инструмент для сбора, обработки и хранения данных о криптовалютах из социальных сетей и новостных источников. Проект помогает отслеживать упоминания монет, анализировать настроение и сохранять результаты для дальнейшего анализа.

## Что делает проект?

- Собирает посты с Reddit и новости с The Block.
- Извлекает упоминания криптовалют, анализирует настроение и темы.
- Сохраняет данные в структурированную базу данных.

## Используемые технологии

- **Язык**: Python
- **Библиотеки**: Selenium, Asyncio, Pandas, Psycopg2
- **База данных**: PostgreSQL
- **API**: Reddit API, другие источники данных

## Как это работает?

1. **Сбор данных**:
   - `RedditCollector`: Парсит посты с Reddit.
   - `BlockCollector`: Собирает новости с The Block.
2. **Обработка**:
   - `DataProcessor`: Извлекает ключевые данные (монеты, настроение).
3. **Хранение**:
   - Данные сохраняются в PostgreSQL для анализа.
