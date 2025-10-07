# Тесты YouTube Dashboard

## Структура

```
tests/
├── __init__.py
├── conftest.py              # Общие фикстуры
├── test_db_manager.py       # Тесты базы данных
├── test_youtube_api.py      # Тесты YouTube API (моки)
├── test_migrations.py       # Тесты системы миграций
└── test_utils.py            # Тесты утилит
```

## Установка зависимостей

```bash
pip install -r requirements-dev.txt
```

## Запуск тестов

### Все тесты

```bash
pytest
```

или

```bash
make test
```

### Только unit тесты (быстрые)

```bash
pytest -m unit
```

или

```bash
make test-unit
```

### Интеграционные тесты

```bash
pytest -m integration
```

или

```bash
make test-integration
```

### С coverage отчётом

```bash
pytest --cov=src --cov-report=html
```

или

```bash
make test-cov
```

Отчёт будет в `htmlcov/index.html`

### Конкретный файл

```bash
pytest tests/test_db_manager.py
```

### Конкретный тест

```bash
pytest tests/test_db_manager.py::TestPersonalChannels::test_add_personal_channel
```

## Типы тестов

### Unit тесты (`@pytest.mark.unit`)
- Быстрые, изолированные
- Тестируют отдельные функции/методы
- Не зависят от внешних сервисов
- Используют моки для БД и API

### Integration тесты (`@pytest.mark.integration`)
- Тестируют взаимодействие компонентов
- Используют реальную (тестовую) БД
- Медленнее unit тестов

### API тесты (`@pytest.mark.api`)
- Тестируют YouTube API
- Используют моки (не делают реальные запросы)
- Проверяют обработку ответов API

### Slow тесты (`@pytest.mark.slow`)
- Долгие тесты (пока нет)
- Можно пропускать: `pytest -m "not slow"`

## Фикстуры

### Основные фикстуры (conftest.py)

- `temp_db_path` - путь к временной БД
- `db` - инициализированная тестовая БД
- `sample_channel_data` - тестовые данные канала
- `sample_subscription_data` - тестовые данные подписки
- `sample_video_data` - тестовые данные видео
- `populated_db` - БД с готовыми тестовыми данными

### Использование фикстур

```python
def test_something(db, sample_channel_data):
    channel_id = db.add_personal_channel(**sample_channel_data)
    assert channel_id > 0
```

## Coverage

Целевой coverage: **>80%**

Текущий coverage по модулям:

- `src/db_manager.py` - **~90%**
- `src/youtube_api.py` - **~75%** (моки API)
- `migrations/migration_manager.py` - **~85%**

Не покрыто coverage:
- CLI скрипты (utils/*)
- Главные entry points (setup_channels.py, sync_subscriptions.py)

## Линтинг

### Flake8

```bash
flake8 src/ utils/ tests/
```

или

```bash
make lint
```

### Black (форматирование)

```bash
black src/ utils/ tests/
```

или

```bash
make format
```

## CI/CD

Тесты автоматически запускаются в GitHub Actions при каждом push.

См. `.github/workflows/test.yml`

## Добавление новых тестов

### 1. Создайте файл `test_*.py`

```python
import pytest

@pytest.mark.unit
def test_my_feature():
    # arrange
    data = {'key': 'value'}
    
    # act
    result = my_function(data)
    
    # assert
    assert result == expected
```

### 2. Используйте фикстуры

```python
def test_with_db(db, sample_channel_data):
    channel_id = db.add_personal_channel(**sample_channel_data)
    assert channel_id > 0
```

### 3. Добавьте маркеры

```python
@pytest.mark.unit  # или integration, api, slow
def test_something():
    pass
```

## Моки для YouTube API

Пример мокирования API ответа:

```python
def test_get_subscriptions(youtube_api):
    mock_response = {
        'items': [{
            'snippet': {
                'resourceId': {'channelId': 'UC_123'},
                'title': 'Test Channel'
            }
        }]
    }
    
    mock_request = Mock()
    mock_request.execute.return_value = mock_response
    youtube_api.service.subscriptions().list.return_value = mock_request
    
    subscriptions = youtube_api.get_subscriptions()
    
    assert len(subscriptions) == 1
```

## Troubleshooting

### Ошибка: "No module named 'src'"

Убедитесь, что запускаете pytest из корня проекта.

### Ошибка: "fixture not found"

Проверьте, что `conftest.py` находится в папке `tests/`.

### Тесты миграций падают

Убедитесь, что папка `migrations/` содержит все файлы миграций.

## Best Practices

1. **Arrange-Act-Assert** паттерн
2. **Один assert на тест** (где возможно)
3. **Описательные имена** тестов
4. **Изолированные тесты** - не зависят друг от друга
5. **Быстрые тесты** - используйте моки для внешних зависимостей
6. **Тестируйте edge cases** - пустые данные, null, ошибки