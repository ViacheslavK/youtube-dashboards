# Quick Start

## 1. Install Dependencies

```bash
pip install -r requirements.txt
```

## 2. Get OAuth Credentials

### Quick Instructions:

1. **Google Cloud Console**: https://console.cloud.google.com/
2. **Create project** (or select existing)
3. **Enable API**:
   - Menu → "APIs & Services" → "Library"
   - Find "YouTube Data API v3"
   - Click "Enable"
4. **Create Credentials**:
   - "APIs & Services" → "Credentials"
   - "+ CREATE CREDENTIALS" → "OAuth client ID"
   - If needed, configure "OAuth consent screen":
     - User Type: **External**
     - App name: SubDeck for YouTube
     - Email: your email
     - Save
   - Application type: **Desktop app**
   - Name: SubDeck for YouTube
   - Download JSON
5. **Save file** as `config/client_secrets.json`

## 3. Installation Check

```bash
python test_setup.py
```

The script will check:
- ✓ Are all dependencies installed
- ✓ Is the folder structure created
- ✓ Is there a credentials file
- ✓ Is the database working

## 4. Channel Setup

```bash
python src/setup_channels.py
```

For each channel:
1. Enter name (e.g., "Technology")
2. Browser will open for OAuth
3. Select Google account
4. Grant access (read-only)
5. Return to terminal

**Tip**: Prepare a list of names for 7 channels in advance.

## 5. Video Loading

```bash
python src/sync_subscriptions.py
```

Choose option **3** for full synchronization (on first run).

This will load:
- All subscriptions from each channel
- Latest 5 videos from each subscription

**Execution time**: ~5-10 minutes (depends on number of subscriptions)

## Done! 🎉

Now you have:
- ✓ 7 configured personal channels
- ✓ All subscriptions in database
- ✓ Latest videos from all subscriptions

### Next steps:

```bash
# View statistics
python utils/view_stats.py

# View errors (if any)
python utils/view_errors.py

# Manage subscriptions
python utils/manage_subscriptions.py
```

---

## Troubleshooting

### "client_secrets.json not found"
→ Check path: should be `config/client_secrets.json`

### OAuth Error in Browser
→ Make sure YouTube Data API v3 is enabled in your project

### "Invalid grant" during authorization
→ Delete old tokens: `rm -rf config/youtube_credentials/*`
→ Run setup_channels.py again

### Quotas exhausted
→ YouTube API: 10,000 units/day (free)
→ Full synchronization: ~700-800 units
→ Wait until next day

---

## Useful commands

```bash
# Check status
python test_setup.py

# Add new channels
python setup_channels.py

# Update subscriptions
python sync_subscriptions.py  # choose option 1

# Load new videos
python sync_subscriptions.py  # choose option 2

# Full synchronization
python sync_subscriptions.py  # choose option 3
```

## Data verification

```python
from database import Database

db = Database()

# Personal channels
channels = db.get_all_personal_channels()
for ch in channels:
    print(f"{ch['name']}: {ch['youtube_channel_id']}")

# Videos for channel #1
videos = db.get_videos_by_personal_channel(1)
print(f"Total videos: {len(videos)}")
for v in videos[:5]:  # First 5
    print(f"  - {v['title']}")
```