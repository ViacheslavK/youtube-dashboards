# YouTube Dashboard

Приложение для отслеживания видео с нескольких личных YouTube каналов в едином интерфейсе.

## Структура проекта

```
youtube-dashboard/
├── src/                          # Основной код
│   ├── __init__.py
│   ├── db_manager.py            # Работа с БД
│   ├── youtube_api.py           # YouTube API интеграция
│   ├── setup_channels.py        # Настройка каналов
│   └── sync_subscriptions.py    # Синхронизация
├── utils/                       # Административные утилиты
│   ├── __init__.py
│   ├── manage_subscriptions.py  # Управление подписками
│   ├── view_errors.py           # Просмотр ошибок
│   └── view_stats.py            # Статистика
├── migrations/                  # Миграции БД
│   ├── __init__.py
│   ├── migration_manager.py
│   ├── 001_initial_schema.py
│   ├── 002_add_subscription_status.py
│   └── 003_add_sync_errors.py
├── config/
│   ├── client_secrets.json      # OAuth credentials (создать вручную)
│   ├── settings.json            # Настройки
│   └── youtube_credentials/     # Токены (создаются автоматически)
├── database/
│   └── videos.db                # SQLite база данных
├── frontend/                    # Веб-интерфейс (в разработке)
├── test_setup.py                # Проверка установки
├── migrate.py                   # Управление миграциями
├── requirements.txt
└── README.md
```

## Установка

### 1. Установка Python зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка YouTube API

#### Шаг 2.1: Создание проекта в Google Cloud Console

1. Зайдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте новый проект или выберите существующий
3. В меню слева найдите "APIs & Services" → "Library"
4. Найдите и включите **YouTube Data API v3**

#### Шаг 2.2: Создание OAuth 2.0 Credentials

1. Перейдите в "APIs & Services" → "Credentials"
2. Нажмите "+ CREATE CREDENTIALS" → "OAuth client ID"
3. Если требуется, настройте OAuth consent screen:
   - User Type: External
   - App name: YouTube Dashboard (или любое другое)
   - User support email: ваш email
   - Developer contact: ваш email
   - Scopes: не нужно добавлять (будут указаны в коде)
4. Application type: **Desktop app**
5. Name: YouTube Dashboard Client
6. Нажмите "CREATE"
7. **Скачайте JSON файл** и сохраните его как `config/client_secrets.json`

**ВАЖНО**: Файл должен называться именно `client_secrets.json` и находиться в папке `config/`

### 3. Первоначальная настройка каналов

Запустите скрипт настройки:

```bash
python setup_channels.py
```

Скрипт попросит вас:
1. Указать количество личных каналов (у вас 12, но используете 7)
2. Для каждого канала:
   - Ввести название (например, "Технологии", "Музыка", "Наука")
   - Пройти OAuth авторизацию в браузере
   - Выбрать нужный Google аккаунт

**Процесс авторизации**:
- Откроется браузер с Google OAuth
- Выберите нужный аккаунт YouTube
- Разрешите доступ к YouTube Data (read-only)
- Браузер перенаправит на localhost - это нормально
- Вернитесь в терминал для продолжения

### 4. Синхронизация подписок и видео

После настройки каналов, загрузите подписки и видео:

```bash
python sync_subscriptions.py
```

Выберите опцию:
- **1** - Обновить только список подписок
- **2** - Загрузить новые видео с существующих подписок
- **3** - Полная синхронизация (рекомендуется при первом запуске)

## Использование

### Проверка данных в БД

Вы можете проверить, что данные загружены, используя любой SQLite клиент или Python:

```python
from database import Database

db = Database()

# Проверить личные каналы
channels = db.get_all_personal_channels()
for ch in channels:
    print(f"{ch['name']}: {ch['youtube_channel_id']}")

# Проверить видео для канала
videos = db.get_videos_by_personal_channel(1, include_watched=True)
print(f"Видео: {len(videos)}")
```

## Следующие шаги

После успешной настройки мы продолжим разработку:

1. ✅ База данных и структура
2. ✅ YouTube API интеграция
3. ✅ Скрипты настройки и синхронизации
4. ⏳ Веб-сервер (Flask)
5. ⏳ Веб-интерфейс (Tweetdeck-style UI)
6. ⏳ Background service для автоматической синхронизации
7. ⏳ Умное определение authuser индекса

## Устранение неполадок

### Ошибка: "client_secrets.json not found"

Убедитесь, что:
- Файл находится в `config/client_secrets.json`
- Путь указан правильно (относительно директории запуска)

### Ошибка при OAuth авторизации

- Проверьте, что YouTube Data API v3 включен в вашем проекте
- Убедитесь, что OAuth consent screen настроен
- Попробуйте удалить старые токены из `config/youtube_credentials/` и авторизоваться заново

### Квоты YouTube API

YouTube API имеет лимит **10,000 units в день** (бесплатно).

Примерные затраты:
- Список подписок: ~1 unit на 50 подписок
- Информация о канале: 1 unit
- Список видео: 1 unit
- Детали видео: 1 unit на запрос

Для 7 каналов с ~50 подписками каждый и проверкой 5 видео:
- Подписки: 7 каналов × 1 unit = 7 units
- Видео: 7 × 50 подписок × 2 units = 700 units
- **Итого**: ~700-800 units на полную синхронизацию

Можно делать полную синхронизацию ~12 раз в день без проблем.

## Лицензия

Личный проект.