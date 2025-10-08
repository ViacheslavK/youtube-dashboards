# 🎨 Plan for Frontend

## Architecture

**Backend:** Flask REST API
**Frontend:** HTML + Vanilla JavaScript (Tweetdeck-style layout)
**Styling:** Tailwind CSS (via CDN)

## Features

1. **Columns for each personal channel** (like Tweetdeck)
2. **Video cards** with thumbnail, title, duration
3. **"Open" and "Mark as watched"** buttons
4. **"Clear watched"** button per column
5. **Auto-refresh** (optional)
6. **Responsive design**

---

## Structure

```sh
youtube-dashboard/
├── src/
│   └── web_server.py         # Flask REST API
├── frontend/
│   ├── index.html            # Main page
│   ├── app.js                # JavaScript logic
│   └── styles.css            # Custom styles
└── static/                   # Static assets (optional)
```

---

## Let's start with Flask REST API

1. `src/web_server.py`:Perfect!
