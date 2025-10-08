# Локализация YouTube Dashboard

## Поддерживаемые языки

- 🇷🇺 **Русский (ru)** - по умолчанию, полный перевод
- 🇬🇧 **English (en)** - полный перевод
- 🇺🇦 **Українська (uk)** - заготовка (можно добавить)

## Использование

### В коде Python:

```python
from locales import t, set_locale

# Простой перевод
print(t('app.name'))  # "YouTube Dashboard"

# С параметрами
print(t('channels.count', count=5))  # "Каналов: 5"

# Смена языка
set_locale('en')
print(t('common.yes'))  # "Yes"
```

### Через утилиту:

```bash
python utils/set_language.py
```

Выберите язык из списка, он сохранится в `config/settings.json`.

## Структура перевода

Файл `ru.json`:
```json
{
  "app": {
    "name": "YouTube Dashboard"
  },
  "common": {
    "yes": "Да",
    "no": "Нет"
  },
  "channels": {
    "count": "Каналов: {count}"
  }
}
```

### Использование:
- `t('app.name')` → "YouTube Dashboard"
- `t('common.yes')` → "Да"
- `t('channels.count', count=5)` → "Каналов: 5"

## Добавление нового языка

### 1. Создайте файл `locales/XX.json`:

```json
{
  "app": {
    "name": "YouTube Dashboard"
  },
  "common": {
    "yes": "...",
    "no": "..."
  }
}
```

Где `XX` - код языка (ISO 639-1): `fr`, `de`, `es`, и т.д.

### 2. Скопируйте структуру из `ru.json`

Используйте `ru.json` или `en.json` как шаблон.

### 3. Переведите все ключи

Важно сохранить:
- ✅ Структуру ключей
- ✅ Плейсхолдеры `{param}`
- ✅ Форматирование

### 4. Тестирование:

```python
from locales import set_locale, t

set_locale('XX')
print(t('app.name'))
```

## Параметры в переводах

Поддерживаются именованные параметры через `.format()`:

```json
{
  "sync": {
    "channels_found": "Найдено {count} каналов"
  }
}
```

```python
t('sync.channels_found', count=5)  # "Найдено 5 каналов"
```

### Множественные параметры:

```json
{
  "test": {
    "multi": "{name} имеет {count} видео"
  }
}
```

```python
t('test.multi', name='Канал', count=10)
```

## Fallback

Если перевод не найден в текущей локали, система:
1. Пытается найти в дефолтной локали (`ru`)
2. Если не найдено - возвращает `[ключ]`

```python
set_locale('en')
t('non.existent.key')  # "[non.existent.key]"
```

## Best Practices

### ✅ Хорошо:

```python
# Используйте t() для всех текстов UI
print(t('sync.complete'))

# Передавайте параметры
print(t('channels.count', count=len(channels)))

# Группируйте по функциональности
"sync.channels_found"
"sync.subscriptions_found"
```

### ❌ Избегайте:

```python
# Не хардкодьте тексты
print("Синхронизация завершена")  # Плохо

# Не форматируйте вручную
print(f"Каналов: {count}")  # Плохо
```

## Структура ключей

Организация по модулям:

```
app.*           - О приложении
common.*        - Общие элементы (кнопки, статусы)
setup.*         - Настройка каналов
sync.*          - Синхронизация
channels.*      - Личные каналы
subscriptions.* - Подписки
videos.*        - Видео
errors.*        - Ошибки
migrations.*    - Миграции БД
stats.*         - Статистика
menu.*          - Меню
```

## Проверка переводов

### Автоматические тесты:

```bash
pytest tests/test_i18n.py
```

### Ручная проверка:

```python
from locales import get_i18n

i18n = get_i18n()
print(i18n.get_available_locales())  # ['ru', 'en', ...]

# Проверить все ключи
for key in ['app.name', 'common.yes', ...]:
    print(f"{key}: {i18n.t(key)}")
```

## Примеры использования

### В скриптах:

```python
# utils/view_stats.py
from locales import t

def main():
    print("=" * 80)
    print(t('stats.title'))
    print("=" * 80)
    
    channels = db.get_all_personal_channels()
    print(t('stats.total_channels', count=len(channels)))
```

### В CLI меню:

```python
print(t('menu.choose_action'))
print(f"1. {t('stats.title')}")
print(f"2. {t('videos.title')}")

choice = input(t('menu.your_choice', min=1, max=2))
```

### В сообщениях об ошибках:

```python
try:
    # ... код ...
except Exception as e:
    print(f"{t('common.error')}: {e}")
```

## Вклад в переводы

Если вы хотите добавить перевод на свой язык:

1. Создайте файл `locales/XX.json`
2. Переведите все ключи из `en.json`
3. Протестируйте
4. Сделайте pull request!

Спасибо за помощь! 🙏