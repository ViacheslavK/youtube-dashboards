
# Copilot Instructions for AI Coding Agents

## Project Overview
SubDeck for YouTube tracks videos across multiple personal YouTube channels. The project is Python-based, uses SQLite, and integrates with YouTube Data API v3.

## Architecture & Key Components
- **src/**: Main code (`db_manager.py`, `youtube_api.py`, `setup_channels.py`, `sync_subscriptions.py`)
- **migrations/**: Database migrations (`migration_manager.py`, numbered migration scripts)
- **utils/**: Admin utilities (`manage_subscriptions.py`, `set_language.py`, etc.)
- **locales/**: Localization files (`ru.json`, `en.json`, `i18n.py`)
- **config/**: OAuth credentials, settings, per-channel tokens
- **database/**: SQLite database (`videos.db`)
- **frontend/**: Web UI (in development)
- **migrate.py**: CLI for managing database migrations

## Developer Workflows

### Install dependencies
```bash
pip install -r requirements.txt
```

### Initial setup
1. Create Google Cloud project, enable YouTube Data API v3, download OAuth credentials as `config/client_secrets.json`.
2. Run:
   ```bash
   python setup_channels.py
   ```
   Follow prompts for channel setup and OAuth authorization.

### Sync data
```bash
python sync_subscriptions.py
```
Choose sync mode (subscriptions, videos, or full sync).

### Database migrations
- Migrations are managed via `migrate.py` and scripts in `migrations/`.
- To apply all pending migrations:
  ```bash
  python migrate.py up
  ```
- To check migration status:
  ```bash
  python migrate.py status
  ```
- To create a new migration template:
  ```bash
  python migrate.py create add_new_feature
  ```
- Migration scripts use an `upgrade(cursor)` function and are auto-discovered by version prefix.

### Localization
- All user-facing messages use the i18n system in `locales/`.
- Supported languages: Russian (`ru`), English (`en`). Add new translations in `locales/*.json`.
- Change language via:
  ```bash
  python utils/set_language.py
  ```
- Access translations in Python:
  ```python
  from locales import t, set_locale
  print(t('common.yes'))  # "Да" or "Yes"
  set_locale('en')
  ```

### Testing & CI
- Tests in `tests/` (unit, integration, API, migration tests).
- Run all tests:
  ```bash
  pytest
  ```
- Coverage and linting via `make test-cov`, `flake8`, `black`.

## Conventions & Patterns
- SQLite schema managed via migrations, not direct code changes.
- Russian is default locale; all new features should support i18n.
- OAuth tokens are per-channel in `config/youtube_credentials/`.
- Scripts are interactive CLI, not web UI (yet).

## Integration Points
- **YouTube Data API v3**: Read-only scope, OAuth managed.
- **Flask**: Listed in requirements, web server in development.
- **Windows Service**: Optional via `pywin32`.

## Troubleshooting
- Ensure `config/client_secrets.json` exists and is valid.
- Delete old tokens in `config/youtube_credentials/` if OAuth issues occur.
- API quota: Full sync for 7 channels uses ~700-800 units.

## Examples
- See `src/db_manager.py` and `migrations/` for DB patterns.
- See `locales/README.md` for i18n usage.
- Run setup, sync, and migration scripts from project root.

---

**If any section is unclear or missing, please provide feedback so instructions can be improved.**
