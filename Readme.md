# YouTube Dashboard

![Tests](https://github.com/ViacheslavK/youtube-dashboards/actions/workflows/test.yml/badge.svg)
![Release](https://github.com/ViacheslavK/youtube-dashboards/actions/workflows/release.yml/badge.svg)
[![codecov](https://codecov.io/gh/ViacheslavK/youtube-dashboards/branch/main/graph/badge.svg)](https://codecov.io/gh/ViacheslavK/youtube-dashboards)

Application for tracking videos from multiple personal YouTube channels in a unified interface.

## Project Structure

```sh

youtube-dashboard/
+-- src/                          # Main code
|   +-- __init__.py
|   +-- db_manager.py            # Database operations
|   +-- youtube_api.py           # YouTube API integration
|   +-- setup_channels.py        # Channel setup
|   +-- sync_subscriptions.py    # Synchronization
+-- utils/                       # Administrative utilities
|   +-- __init__.py
|   +-- manage_subscriptions.py  # Subscription management
|   +-- view_errors.py           # Error viewing
|   +-- view_stats.py            # Statistics
+-- migrations/                  # Database migrations
|   +-- __init__.py
|   +-- migration_manager.py
|   +-- 001_initial_schema.py
|   +-- 002_add_subscription_status.py
|   +-- 003_add_sync_errors.py
+-- config/
|   +-- client_secrets.json      # OAuth credentials (create manually)
|   +-- settings.json            # Settings
|   +-- youtube_credentials/     # Tokens (created automatically)
+-- database/
|   +-- videos.db                # SQLite database
+-- frontend/                    # Web interface (in development)
+-- test_setup.py                # Installation check
+-- migrate.py                   # Migration management
+-- requirements.txt
+-- README.md
```

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure YouTube API

#### Step 2.1: Create Project in Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. In the left menu, find "APIs & Services" → "Library"
4. Find and enable **YouTube Data API v3**

#### Step 2.2: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "+ CREATE CREDENTIALS" → "OAuth client ID"
3. If required, configure OAuth consent screen:
    - User Type: External
    - App name: YouTube Dashboard (or any other)
    - User support email: your email
    - Developer contact: your email
    - Scopes: no need to add (will be specified in code)
4. Application type: **Desktop app**
5. Name: YouTube Dashboard Client
6. Click "CREATE"
7. **Download the JSON file** and save it as `config/client_secrets.json`

**IMPORTANT**: The file must be named exactly `client_secrets.json` and located in the `config/` folder

### 3. Initial Channel Setup

Run the setup script:

```bash
python setup_channels.py
```

The script will ask you to:

1. Specify the number of personal channels (you have 12, but use 7)
2. For each channel:
    - Enter a name (for example, "Technology", "Music", "Science")
    - Complete OAuth authorization in the browser
    - Select the desired Google account

**Authorization process**:

- Browser will open with Google OAuth
- Select the desired YouTube account
- Grant access to YouTube Data (read-only)
- Browser will redirect to localhost - this is normal
- Return to terminal to continue

### 4. Synchronize Subscriptions and Videos

After setting up channels, load subscriptions and videos:

```bash
python sync_subscriptions.py
```

Choose an option:

- **1** - Update subscription list only
- **2** - Load new videos from existing subscriptions
- **3** - Full synchronization (recommended for first run)

## Usage

### Checking Database Data

You can verify that data has been loaded using any SQLite client or Python:

```python
from database import Database

db = Database()

# Check personal channels
channels = db.get_all_personal_channels()
for ch in channels:
    print(f"{ch['name']}: {ch['youtube_channel_id']}")

# Check videos for channel
videos = db.get_videos_by_personal_channel(1, include_watched=True)
print(f"Videos: {len(videos)}")
```

## Next Steps

After successful setup, we will continue development:

1. ✅ Database and structure
2. ✅ YouTube API integration
3. ✅ Setup and synchronization scripts
4. ⏳ Web server (Flask)
5. ⏳ Web interface (Tweetdeck-style UI)
6. ⏳ Background service for automatic synchronization
7. ⏳ Smart authuser index detection

## Troubleshooting

### Error: "client_secrets.json not found"

Make sure that:

- File is located in `config/client_secrets.json`
- Path is correct (relative to launch directory)

### OAuth Authorization Error

- Check that YouTube Data API v3 is enabled in your project
- Ensure OAuth consent screen is configured
- Try deleting old tokens from `config/youtube_credentials/` and re-authorize

### YouTube API Quotas

YouTube API has a limit of **10,000 units per day** (free).

Approximate costs:

- Subscription list: ~1 unit per 50 subscriptions
- Channel information: 1 unit
- Video list: 1 unit
- Video details: 1 unit per request

For 7 channels with ~50 subscriptions each and checking 5 videos:

- Subscriptions: 7 channels × 1 unit = 7 units
- Videos: 7 × 50 subscriptions × 2 units = 700 units
- **Total**: ~700-800 units for full synchronization

You can perform full synchronization ~12 times per day without issues.

## License

Personal project.
