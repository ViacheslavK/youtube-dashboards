# 🚀 SubDeck for YouTube Setup Instructions

## 📋 Prerequisites

- Python 3.8+
- Virtual environment (already created as `venv/`)

## 🛠️ Initial Setup (One-time)

### 1. Activate Virtual Environment
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up YouTube API Credentials
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create/select project
3. Enable YouTube Data API v3
4. Create OAuth 2.0 credentials (Desktop app)
5. Download `client_secrets.json` → save as `config/client_secrets.json`

### 4. Initialize Database
```bash
python migrate.py
```

### 5. Set up Channels (if not done)
```bash
python src/setup_channels.py
```

### 6. Sync Data (if not done)
```bash
python src/sync_subscriptions.py
# Choose option 3 for full sync
```

## 🎬 Running the Application

### Always start with virtual environment:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### Start the web server:
```bash
python src/web_server.py
```

### Access the application:
- **Main Dashboard**: http://localhost:8080
- **Admin Panel**: http://localhost:8080/admin.html
- **Component Tests**: http://localhost:8080/test-components.html

## 🧪 Testing

### Run unit tests:
```bash
python -m pytest tests/
```

### Run with coverage:
```bash
python -m pytest tests/ --cov=src --cov-report=html
```

## 🛠️ Development Commands

### View statistics:
```bash
python utils/view_stats.py
```

### View errors:
```bash
python utils/view_errors.py
```

### Manage subscriptions:
```bash
python utils/manage_subscriptions.py
```

### Set language:
```bash
python utils/set_language.py
```

## 📁 Project Structure

```
youtube-dashboard/
├── config/                 # Configuration files
│   ├── client_secrets.json # YouTube API credentials
│   ├── settings.json      # App settings
│   └── youtube_credentials/ # OAuth tokens
├── database/              # SQLite database
├── frontend/              # Web interface
│   ├── index.html         # Main dashboard
│   ├── admin.html         # Admin panel
│   ├── js/                # JavaScript files
│   └── css/               # Stylesheets
├── src/                   # Python source code
├── utils/                 # Administrative utilities
├── tests/                 # Test files
└── locales/               # Internationalization
```

## 🔧 Troubleshooting

### "Module not found" errors:
```bash
# Make sure virtual environment is activated
venv\Scripts\activate
pip install -r requirements.txt
```

### Database issues:
```bash
# Reset database
rm -rf database/
python migrate.py
```

### OAuth issues:
```bash
# Clear old tokens
rm -rf config/youtube_credentials/
python src/setup_channels.py
```

### Port already in use:
```bash
# Kill process on port 8080
# Windows: netstat -ano | findstr :8080
# Linux/Mac: lsof -ti:8080 | xargs kill -9
```

## 📝 Notes

- Always activate virtual environment before running any Python commands
- Keep `client_secrets.json` secure and never commit to version control
- Database file (`videos.db`) is created automatically
- Frontend uses CDN links, so internet connection required for full functionality