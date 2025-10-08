# YouTube Dashboard Localization

## Supported Languages

- 🇷🇺 **Russian (ru)** - default, complete translation
- 🇬🇧 **English (en)** - complete translation
- 🇺🇦 **Ukrainian (uk)** - template (can be added)

## Usage

### In Python Code

```python
from locales import t, set_locale

# Simple translation
print(t('app.name'))  # "YouTube Dashboard"

# With parameters
print(t('channels.count', count=5))  # "Channels: 5"

# Change language
set_locale('en')
print(t('common.yes'))  # "Yes"
```

### Via Utility

```bash
python utils/set_language.py
```

Select language from the list, it will be saved in `config/settings.json`.

## Translation Structure

File `ru.json`:

```json
{
  "app": {
    "name": "YouTube Dashboard"
  },
  "common": {
    "yes": "Yes",
    "no": "No"
  },
  "channels": {
    "count": "Channels: {count}"
  }
}
```

### Display

- `t('app.name')` → "YouTube Dashboard"
- `t('common.yes')` → "Yes"
- `t('channels.count', count=5)` → "Channels: 5"

## Adding a New Language

### 1. Create file `locales/XX.json`

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

Where `XX` is the language code (ISO 639-1): `fr`, `de`, `es`, etc.

### 2. Copy structure from `ru.json`

Use `ru.json` or `en.json` as a template.

### 3. Translate all keys

Important to preserve:

- ✅ Key structure
- ✅ Placeholders `{param}`
- ✅ Formatting

### 4. Testing

```python
from locales import set_locale, t

set_locale('XX')
print(t('app.name'))
```

## Parameters in Translations

Named parameters are supported via `.format()`:

```json
{
  "sync": {
    "channels_found": "Found {count} channels"
  }
}
```

```python
t('sync.channels_found', count=5)  # "Found 5 channels"
```

### Multiple Parameters

```json
{
  "test": {
    "multi": "{name} has {count} videos"
  }
}
```

```python
t('test.multi', name='Channel', count=10)
```

## Fallback

If translation is not found in current locale, the system:

1. Tries to find in default locale (`ru`)
2. If not found - returns `[key]`

```python
set_locale('en')
t('non.existent.key')  # "[non.existent.key]"
```

## Best Practices

### ✅ Good

```python
# Use t() for all UI texts
print(t('sync.complete'))

# Pass parameters
print(t('channels.count', count=len(channels)))

# Group by functionality
"sync.channels_found"
"sync.subscriptions_found"
```

### ❌ Avoid

```python
# Don't hardcode texts
print("Synchronization completed")  # Bad

# Don't format manually
print(f"Channels: {count}")  # Bad
```

## Key Structure

Organization by modules:

```sh
app.*           - About the application
common.*        - Common elements (buttons, statuses)
setup.*         - Channel setup
sync.*          - Synchronization
channels.*      - Personal channels
subscriptions.* - Subscriptions
videos.*        - Videos
errors.*        - Errors
migrations.*    - Database migrations
stats.*         - Statistics
menu.*          - Menu
```

## Translation Verification

### Automated Tests

```bash
pytest tests/test_i18n.py
```

### Manual Verification

```python
from locales import get_i18n

i18n = get_i18n()
print(i18n.get_available_locales())  # ['ru', 'en', ...]

# Check all keys
for key in ['app.name', 'common.yes', ...]:
    print(f"{key}: {i18n.t(key)}")
```

## Usage Examples

### In Scripts

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

### In CLI Menu

```python
print(t('menu.choose_action'))
print(f"1. {t('stats.title')}")
print(f"2. {t('videos.title')}")

choice = input(t('menu.your_choice', min=1, max=2))
```

### In Error Messages

```python
try:
    # ... code ...
except Exception as e:
    print(f"{t('common.error')}: {e}")
```

## Contributing to Translations

If you want to add translation for your language:

1. Create file `locales/XX.json`
2. Translate all keys from `en.json`
3. Test it
4. Make a pull request!

Thank you for your help! 🙏
