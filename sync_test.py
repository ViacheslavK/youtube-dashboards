from src.db_manager import Database
   
db = Database()

# Проверь каналы
channels = db.get_all_personal_channels()
print(f"Всего каналов: {len(channels)}")

# Проверь видео
for ch in channels:
    videos = db.get_videos_by_personal_channel(ch['id'])
    print(f"{ch['name']}: {len(videos)} видео")