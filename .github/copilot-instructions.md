# Copilot Instructions for AI Coding Agents

## Project Overview
This is a YouTube Dashboard for tracking videos across multiple personal YouTube channels in a unified interface. The project is primarily in Python and uses SQLite for storage and the YouTube Data API v3 for integration.

## Architecture & Key Components
- **config/**: Contains OAuth credentials (`client_secrets.json`) and per-channel tokens (`youtube_credentials/`).
- **database/**: Stores `videos.db` (SQLite). All persistent data is managed here.
- **src/database.py**: Defines the `Database` class for all DB operations. Tables include `personal_channels`, `subscriptions`, and `videos`.
- **src/youtube_api.py**: Handles YouTube API authentication and data fetching. Uses OAuth 2.0 and stores tokens in `config/youtube_credentials/`.
- **src/setup_channels.py**: Interactive setup for personal channels. Guides user through OAuth, channel naming, and color assignment.
- **src/sync_subscriptions.py**: Synchronizes subscriptions and videos for all configured channels. Offers options for partial or full sync.

## Developer Workflows
- **Install dependencies:**
  ```bash
  pip install -r requirements.txt
  ```
- **Initial setup:**
  1. Create Google Cloud project, enable YouTube Data API v3, and download OAuth credentials as `config/client_secrets.json`.
  2. Run:
     ```bash
     python setup_channels.py
     ```
     Follow prompts for channel setup and OAuth authorization.
- **Sync data:**
  ```bash
  python sync_subscriptions.py
  ```
  Choose sync mode (subscriptions, videos, or full sync).
- **Database access:**
  Use the `Database` class in `src/database.py` for querying channels and videos. Example:
  ```python
  from database import Database
  db = Database()
  channels = db.get_all_personal_channels()
  videos = db.get_videos_by_personal_channel(1, include_watched=True)
  ```

## Conventions & Patterns
- All persistent data is stored in SQLite (`database/videos.db`).
- OAuth tokens are stored per-channel in `config/youtube_credentials/`.
- Channel colors are assigned from a fixed palette in `setup_channels.py`.
- Russian is used for user-facing messages and some comments.
- Scripts are designed for interactive terminal use, not web UI (yet).

## Integration Points
- **YouTube Data API v3**: All API calls use read-only scope. Credentials and tokens are managed via Google OAuth.
- **Flask**: Listed in requirements, but web server is not yet implemented.
- **Windows Service**: Optional support via `pywin32` for future background sync.

## Troubleshooting
- Ensure `config/client_secrets.json` exists and is valid.
- Delete old tokens in `config/youtube_credentials/` if OAuth issues occur.
- API quota: Full sync for 7 channels uses ~700-800 units (well below daily free limit).

## Examples
- See `src/database.py` and `src/youtube_api.py` for main data and API patterns.
- Run setup and sync scripts from the project root for correct path resolution.

---

**If any section is unclear or missing, please provide feedback so instructions can be improved.**
