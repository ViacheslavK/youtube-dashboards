# Быстрый старт

## 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

## 2. Получение OAuth Credentials

### Быстрая инструкция:

1. **Google Cloud Console**: https://console.cloud.google.com/
2. **Создать проект** (или выбрать существующий)
3. **Включить API**:
   - Меню → "APIs & Services" → "Library"
   - Найти "YouTube Data API v3"
   - Нажать "Enable"
4. **Создать Credentials**:
   - "APIs & Services" → "Credentials"
   - "+ CREATE CREDENTIALS" → "OAuth client ID"
   - Если нужно, настроить "OAuth consent screen":
     - User Type: **External**
     - App name: YouTube Dashboard
     - Email: ваш email
     - Сохранить
   - Application type: **Desktop app**
   - Имя: YouTube Dashboard
   - Скачать JSON
5. **Сохранить файл** как `config/client_secrets.json`

## 3. Проверка установки

```bash
python test_setup.py
```

Скрипт проверит:
- ✓ Установлены ли все зависимости
- ✓ Создана ли структура папок
- ✓ Есть ли файл credentials
- ✓ Работает ли база данных

## 4. Настройка каналов

```bash
python setup_channels.py
```

Для каждого канала:
1. Введите название (например, "Технологии")
2. Откроется браузер для OAuth
3. Выберите Google аккаунт
4. Разрешите доступ (read-only)
5. Вернитесь в терминал

**Совет**: Подготовьте список названий для 7 каналов заранее.

## 5. Загрузка видео

```bash
python sync_subscriptions.py
```

Выберите опцию **3** для полной синхронизации (при первом запуске).

Это загрузит:
- Все подписки с каждого канала
- Последние 5 видео с каждой подписки

**Время выполнения**: ~5-10 минут (зависит от количества подписок)

## Готово! 🎉

Теперь у вас есть:
- ✓ 7 настроенных личных каналов
- ✓ Все подписки в базе данных
- ✓ Последние видео со всех подписок

### Следующие шаги:

- Запустить веб-интерфейс (в разработке)
- Настроить автоматическую синхронизацию (в разработке)

---

## Устранение проблем

### "client_secrets.json not found"
→ Проверьте путь: должен быть `config/client_secrets.json`

### Ошибка OAuth в браузере
→ Убедитесь, что YouTube Data API v3 включен в вашем проекте

### "Invalid grant" при авторизации
→ Удалите старые токены: `rm -rf config/youtube_credentials/*`
→ Запустите setup_channels.py снова

### Квоты исчерпаны
→ YouTube API: 10,000 units/день (бесплатно)
→ Полная синхронизация: ~700-800 units
→ Подождите до следующего дня

---

## Полезные команды

```bash
# Проверка статуса
python test_setup.py

# Добавить новые каналы
python setup_channels.py

# Обновить подписки
python sync_subscriptions.py  # выбрать опцию 1

# Загрузить новые видео
python sync_subscriptions.py  # выбрать опцию 2

# Полная синхронизация
python sync_subscriptions.py  # выбрать опцию 3
```

## Проверка данных

```python
from database import Database

db = Database()

# Личные каналы
channels = db.get_all_personal_channels()
for ch in channels:
    print(f"{ch['name']}: {ch['youtube_channel_id']}")

# Видео для канала #1
videos = db.get_videos_by_personal_channel(1)
print(f"Всего видео: {len(videos)}")
for v in videos[:5]:  # Первые 5
    print(f"  - {v['title']}")
```
