# Руководство по миграциям базы данных

## Концепция

YouTube Dashboard использует систему версионированных миграций для управления изменениями схемы базы данных.

### Принципы:

1. **Каждая миграция** = отдельный файл с номером версии
2. **Последовательное применение** - миграции применяются по порядку
3. **Идемпотентность** - можно запускать повторно безопасно
4. **Только добавление** - миграции не удаляют данные пользователя
5. **Отслеживание версий** - таблица `schema_version` хранит историю

## Использование

### Проверить статус миграций

```bash
python migrate.py status
```

Показывает:
- Текущую версию схемы БД
- Доступные миграции
- Неприменённые миграции
- Историю применённых миграций

### Применить все миграции

```bash
python migrate.py up
```

Применяет все неприменённые миграции последовательно.

### Применить до конкретной версии

```bash
python migrate.py up --target 3
```

Применяет миграции до версии 3 включительно.

## Сценарий обновления приложения

### Ситуация: Пользователь обновляется с версии 1.0 до 3.0

```
Версия 1.0 (схема v1) → Версия 2.0 (схема v2) → Версия 3.0 (схема v3)
```

**Что происходит:**

1. Пользователь скачивает версию 3.0
2. При первом запуске (или вручную) выполняет: `python migrate.py up`
3. Система определяет текущую версию БД: `v1`
4. Применяет миграции: `v1 → v2 → v3` последовательно
5. Данные пользователя сохраняются, добавляются только новые поля/таблицы

**Безопасность:**
- Если миграция v2 не удалась → процесс останавливается
- Пользователь может исправить проблему и запустить снова
- Уже применённые миграции пропускаются

## Создание новой миграции

### Автоматическое создание шаблона

```bash
python migrate.py create add_user_settings
```

Создаст файл: `migrations/004_add_user_settings.py`

### Структура миграции

```python
"""
Миграция 004: Add User Settings

Описание изменений
"""

def upgrade(cursor):
    """Применение миграции"""
    
    # Добавление поля
    cursor.execute('''
        ALTER TABLE personal_channels 
        ADD COLUMN default_view TEXT DEFAULT 'grid'
    ''')
    
    # Создание таблицы
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT
        )
    ''')
    
    # Создание индекса
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_settings_key 
        ON user_settings(key)
    ''')
    
    print("  ✓ Добавлены настройки пользователя")
```

## Существующие миграции

### 001: Initial Schema
- Создание базовых таблиц: `personal_channels`, `subscriptions`, `videos`
- Индексы для оптимизации

### 002: Add Subscription Status
- Поля: `is_active`, `deleted_by_user`, `deactivated_at`
- Отслеживание статуса подписок

### 003: Add Sync Errors
- Таблица `sync_errors` для логирования ошибок
- Индексы для быстрого поиска

## Лучшие практики

### ✅ Делайте:

1. **Используйте `IF NOT EXISTS`** для таблиц и индексов
2. **Проверяйте наличие колонок** перед добавлением (PRAGMA table_info)
3. **Добавляйте DEFAULT значения** для новых полей
4. **Документируйте изменения** в docstring миграции
5. **Тестируйте на копии БД** перед релизом

### ❌ Не делайте:

1. **Не удаляйте колонки** (SQLite не поддерживает DROP COLUMN легко)
2. **Не изменяйте типы данных** существующих колонок
3. **Не удаляйте данные пользователя**
4. **Не меняйте уже применённые миграции** - создавайте новую
5. **Не полагайтесь на конкретный порядок записей** в БД

## Откат миграций

Откат (downgrade) **не реализован** по умолчанию, так как:
- SQLite ограниченно поддерживает ALTER TABLE
- DROP COLUMN не поддерживается
- Риск потери данных

Если нужен откат:
1. Сделайте резервную копию БД
2. Восстановите из копии
3. Примените нужные миграции

## Резервное копирование

**Всегда делайте бэкап перед миграцией!**

```bash
# Автоматический бэкап (рекомендуется добавить в migrate.py)
cp database/videos.db database/videos.db.backup
```

## Структура таблицы schema_version

```sql
CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,    -- Номер версии миграции
    name TEXT NOT NULL,             -- Название миграции
    applied_at TIMESTAMP            -- Когда применена
);
```

Пример данных:

| version | name | applied_at |
|---------|------|------------|
| 1 | initial_schema | 2025-01-15 10:30:00 |
| 2 | add_subscription_status | 2025-01-20 14:15:00 |
| 3 | add_sync_errors | 2025-01-25 09:45:00 |

## Troubleshooting

### Ошибка: "Migration X failed"

1. Проверьте лог ошибки
2. Исправьте проблему (возможно, синтаксис SQL)
3. Запустите `python migrate.py up` снова
4. Уже применённые миграции будут пропущены

### Ошибка: "Table already exists"

- Это нормально, если используется `CREATE TABLE IF NOT EXISTS`
- Проверьте, что миграция идемпотентна

### "Несоответствие версий после обновления"

```bash
# Проверьте статус
python migrate.py status

# Примените недостающие миграции
python migrate.py up
```

### Полная переустановка схемы (⚠️ УДАЛИТ ВСЕ ДАННЫЕ)

```bash
# Бэкап
cp database/videos.db database/videos.db.backup

# Удалить БД
rm database/videos.db

# Создать заново
python migrate.py up
```

## Интеграция в CI/CD

### Автоматическая проверка при деплое

```bash
# В скрипте деплоя
python migrate.py status
python migrate.py up --yes  # (если добавить флаг --yes)
```

## Примеры реальных сценариев

### Сценарий 1: Добавление новой функции

**Задача:** Добавить избранные видео

```bash
# Создаём миграцию
python migrate.py create add_favorites

# Редактируем migrations/004_add_favorites.py:
```

```python
def upgrade(cursor):
    cursor.execute('''
        ALTER TABLE videos 
        ADD COLUMN is_favorite BOOLEAN DEFAULT 0
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_videos_favorite 
        ON videos(is_favorite, published_at DESC)
    ''')
    
    print("  ✓ Добавлена функция избранного")
```

```bash
# Применяем
python migrate.py up
```

### Сценарий 2: Рефакторинг структуры

**Задача:** Разделить канал и email в разные таблицы

```bash
python migrate.py create separate_user_accounts
```

```python
def upgrade(cursor):
    # Создаём новую таблицу
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            display_name TEXT
        )
    ''')
    
    # Добавляем связь к существующей таблице
    cursor.execute('''
        ALTER TABLE personal_channels 
        ADD COLUMN user_account_id INTEGER 
        REFERENCES user_accounts(id)
    ''')
    
    # Миграция данных (если нужно)
    # ... логика переноса ...
    
    print("  ✓ Разделены аккаунты пользователей")
```

### Сценарий 3: Оптимизация производительности

**Задача:** Добавить индекс для быстрого поиска

```bash
python migrate.py create optimize_video_search
```

```python
def upgrade(cursor):
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_videos_title_search 
        ON videos(title)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_videos_channel_date 
        ON videos(subscription_id, published_at DESC, is_watched)
    ''')
    
    print("  ✓ Добавлены индексы для оптимизации")
```

## FAQ

**Q: Можно ли пропустить миграцию?**
A: Нет, миграции применяются последовательно. Это гарантирует целостность.

**Q: Что если у меня старая версия БД без schema_version?**
A: Система автоматически создаст таблицу и определит версию как 0.

**Q: Как откатиться к предыдущей версии?**
A: Восстановите из бэкапа. Полноценный rollback не поддерживается.

**Q: Сколько миграций можно создать?**
A: Практически неограниченно. Версии от 001 до 999.

**Q: Нужно ли коммитить миграции в Git?**
A: Да! Миграции - часть кода приложения.

**Q: Как тестировать миграции?**
A: Создайте копию БД и тестируйте на ней перед продакшеном.

## Структура файлов

```
youtube-dashboard/
├── migrations/
│   ├── __init__.py
│   ├── migration_manager.py      # Система управления
│   ├── 001_initial_schema.py
│   ├── 002_add_subscription_status.py
│   ├── 003_add_sync_errors.py
│   └── 004_your_new_migration.py
├── migrate.py                     # CLI утилита
└── database/
    └── videos.db                  # БД с таблицей schema_version
```

## Заключение

Система миграций обеспечивает:
- ✅ Безопасное обновление приложения
- ✅ Сохранность данных пользователей
- ✅ Прозрачность изменений
- ✅ Возможность пропуска версий (например, 1.0 → 3.0)
- ✅ Откат через бэкапы

**Помните:** Всегда делайте бэкап перед миграцией в продакшене!
