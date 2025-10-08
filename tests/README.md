# YouTube Dashboard Tests

## Structure

```
tests/
├── __init__.py
├── conftest.py              # Common fixtures
├── test_db_manager.py       # Database tests
├── test_youtube_api.py      # YouTube API tests (mocks)
├── test_migrations.py       # Migration system tests
└── test_utils.py            # Utilities tests
```

---

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

## Dependencies Installation

```bash
pip install -r requirements-dev.txt
```

## Running Tests

### All Tests

```bash
pytest
```

or

```bash
make test
```

### Unit Tests Only (Fast)

```bash
pytest -m unit
```

or

```bash
make test-unit
```

### Integration Tests

```bash
pytest -m integration
```

or

```bash
make test-integration
```

### With Coverage Report

```bash
pytest --cov=src --cov-report=html
```

or

```bash
make test-cov
```

Report will be in `htmlcov/index.html`

### Specific File

```bash
pytest tests/test_db_manager.py
```

### Specific Test

```bash
pytest tests/test_db_manager.py::TestPersonalChannels::test_add_personal_channel
```

## Test Types

### Unit Tests (`@pytest.mark.unit`)
- Fast, isolated
- Test individual functions/methods
- No external service dependencies
- Use mocks for DB and API

### Integration Tests (`@pytest.mark.integration`)
- Test component interactions
- Use real (test) database
- Slower than unit tests

### API Tests (`@pytest.mark.api`)
- Test YouTube API
- Use mocks (no real requests)
- Verify API response handling

### Slow Tests (`@pytest.mark.slow`)
- Long-running tests (none currently)
- Can be skipped: `pytest -m "not slow"`

## Fixtures

### Main Fixtures (conftest.py)

- `temp_db_path` - path to temporary database
- `db` - initialized test database
- `sample_channel_data` - test channel data
- `sample_subscription_data` - test subscription data
- `sample_video_data` - test video data
- `populated_db` - database with ready test data

### Fixture Usage

```python
def test_something(db, sample_channel_data):
    channel_id = db.add_personal_channel(**sample_channel_data)
    assert channel_id > 0
```

## Coverage

Target coverage: **>80%**

Current coverage by modules:

- `src/db_manager.py` - **~90%**
- `src/youtube_api.py` - **~75%** (API mocks)
- `migrations/migration_manager.py` - **~85%**

Not covered by coverage:
- CLI scripts (utils/*)
- Main entry points (setup_channels.py, sync_subscriptions.py)

## Linting

### Flake8

```bash
flake8 src/ utils/ tests/
```

or

```bash
make lint
```

### Black (Formatting)

```bash
black src/ utils/ tests/
```

or

```bash
make format
```

## CI/CD

Tests are automatically run in GitHub Actions on each push.

See `.github/workflows/test.yml`

## Adding New Tests

### 1. Create file `test_*.py`

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

### 2. Use Fixtures

```python
def test_with_db(db, sample_channel_data):
    channel_id = db.add_personal_channel(**sample_channel_data)
    assert channel_id > 0
```

### 3. Add Markers

```python
@pytest.mark.unit  # or integration, api, slow
def test_something():
    pass
```

## YouTube API Mocks

Example of mocking API response:

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

### Error: "No module named 'src'"

Make sure you're running pytest from the project root.

### Error: "fixture not found"

Check that `conftest.py` is in the `tests/` folder.

### Migration tests failing

Make sure the `migrations/` folder contains all migration files.

## Best Practices

1. **Arrange-Act-Assert** pattern
2. **One assert per test** (where possible)
3. **Descriptive test names**
4. **Isolated tests** - don't depend on each other
5. **Fast tests** - use mocks for external dependencies
6. **Test edge cases** - empty data, null, errors
