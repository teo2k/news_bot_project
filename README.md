# news_bot_project
News bot project description 

news_bot_project/
├── collectors/                    # Модули сбора данных
│   ├── news_collector.py          # Коллектор для новостных сайтов
│   ├── reddit_collector.py        # Коллектор для Reddit
│   ├── telegram_collector.py      # Коллектор для Telegram (пока не реализован)
│   ├── discord_collector.py       # Коллектор для Discord (пока не реализован)
│   └── merger.py                  # Объединение новости с курсом и добавление в создаваемый dt
├── processor/                     # Модуль обработки данных
│   ├── data_processor.py          # Основной процессор данных
│   └── filters.py                 # Фильтры и метрики
├── database/                      # Модуль базы данных
│   └── db.py                      # Подключение к базе данных
├── telegram/                      # Модуль инциализации и работы самого бота
│   └── bot.py                     # Основной код телеграм-бота и его функций
├── config/                        # Конфигурационные файлы
│   ├── config.yaml                # Основной файл конфигурации
│   ├── news.yaml                  # Настройки для новостных сайтов
│   └── logging.yaml               # Настройки логирования
├── logs/                          # Логи
│   ├── app.log                    # Основной лог
│   └── errors.log                 # Лог ошибок
├── cache/                         # Кэщ (опционально)
│   ├── twitter_ids.json           # Кеш айдишников твиттера для теста (не используется)
├── requirements.txt               # Зависимости проекта
├── main.py                        # Точка входа для запуска проекта
└── README.md                      # Документация проекта
