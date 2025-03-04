import logging
import logging.config
import yaml
from pathlib import Path
import asyncio
from collectors.merge import merge_data
from database.db import CryptoDB

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
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Запуск проекта...")

    # Инициализация базы данных (без явного config)
    db = CryptoDB()
    db.initialize_db()
    logger.info("База данных инициализирована")

    # Запуск системы сбора и обработки данных
    logger.info("Запуск системы сбора и обработки данных...")
    merge_task = asyncio.create_task(merge_data())

    try:
        # Ждём завершения задачи или ловим исключения
        await merge_task
        logger.info("Система сбора данных завершена.")
    except Exception as e:
        logger.error(f"Ошибка в системе сбора данных: {e}", exc_info=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger = logging.getLogger(__name__)
        logger.info("Остановка проекта...")
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Неожиданная ошибка: {e}", exc_info=True)
