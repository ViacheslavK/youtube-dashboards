#!/usr/bin/env python3
"""
Просмотр статистики по загруженным данным
"""

import sys
import os

# Добавляем корневую папку проекта в путь
# __file__ = D:\...\utils\view_stats.py
# dirname = D:\...\utils
# dirname(dirname) = D:\...\youtube-dashboard-claude
current_dir = os.path.dirname(os.path.abspath(__file__))  # utils/
project_root = os.path.dirname(current_dir)  # корень проекта
sys.path.insert(0, project_root)

from src.db_manager import Database


def view_channels_stats():
    """Статистика по каналам"""
    db = Database()
    
    channels = db.get_all_personal_channels()
    print(f"\n{'=' * 80}")
    print(f"Всего личных каналов: {len(channels)}")
    print('=' * 80)
    
    if not channels:
        print("\n⚠️  Нет настроенных каналов")
        print("Запустите: python src/setup_channels.py")
        return
    
    total_videos = 0
    total_subscriptions = 0
    total_unwatched = 0
    
    for ch in channels:
        videos = db.get_videos_by_personal_channel(ch['id'], include_watched=True)
        unwatched = db.get_videos_by_personal_channel(ch['id'], include_watched=False)
        subs = db.get_subscriptions_by_channel(ch['id'], include_inactive=False)
        
        print(f"\n📺 {ch['name']} (ID: {ch['id']})")
        print(f"   YouTube Channel: {ch['youtube_channel_id']}")
        print(f"   Цвет: {ch['color']}")
        print(f"   Подписок: {len(subs)}")
        print(f"   Видео: {len(videos)} (не просмотрено: {len(unwatched)})")
        
        if ch['authuser_index'] is not None:
            print(f"   authuser индекс: {ch['authuser_index']}")
        
        total_videos += len(videos)
        total_subscriptions += len(subs)
        total_unwatched += len(unwatched)
    
    print(f"\n{'=' * 80}")
    print(f"ИТОГО:")
    print(f"   Подписок: {total_subscriptions}")
    print(f"   Видео: {total_videos}")
    print(f"   Не просмотрено: {total_unwatched}")
    print('=' * 80)


def view_recent_videos(limit: int = 20):
    """Показать последние видео"""
    db = Database()
    channels = db.get_all_personal_channels()
    
    if not channels:
        print("\n⚠️  Нет настроенных каналов")
        return
    
    print(f"\n{'=' * 80}")
    print(f"Последние {limit} видео")
    print('=' * 80)
    
    all_videos = []
    for ch in channels:
        videos = db.get_videos_by_personal_channel(ch['id'], include_watched=True)
        for v in videos:
            v['personal_channel_name'] = ch['name']
        all_videos.extend(videos)
    
    # Сортируем по дате публикации
    all_videos.sort(key=lambda x: x['published_at'], reverse=True)
    
    for v in all_videos[:limit]:
        watched = "✓" if v['is_watched'] else "📹"
        print(f"\n{watched} [{v['personal_channel_name']}] {v['title']}")
        print(f"   Канал: {v['channel_name']}")
        print(f"   Дата: {v['published_at'][:10]} | Длина: {v['duration']}")


def view_subscriptions():
    """Показать все подписки"""
    db = Database()
    channels = db.get_all_personal_channels()
    
    print(f"\n{'=' * 80}")
    print("Подписки по каналам")
    print('=' * 80)
    
    for ch in channels:
        subs = db.get_subscriptions_by_channel(ch['id'], include_inactive=False)
        
        if subs:
            print(f"\n📺 {ch['name']}: {len(subs)} подписок")
            for i, sub in enumerate(subs[:10], 1):
                print(f"   {i}. {sub['channel_name']}")
            
            if len(subs) > 10:
                print(f"   ... и ещё {len(subs) - 10}")


def main():
    print("=" * 80)
    print("YouTube Dashboard - Статистика")
    print("=" * 80)
    
    print("\nВыберите действие:")
    print("1. Статистика по каналам")
    print("2. Последние 20 видео")
    print("3. Последние 50 видео")
    print("4. Список подписок")
    print("5. Выход")
    
    choice = input("\nВаш выбор (1-5): ").strip()
    
    if choice == '1':
        view_channels_stats()
    elif choice == '2':
        view_recent_videos(20)
    elif choice == '3':
        view_recent_videos(50)
    elif choice == '4':
        view_subscriptions()
    elif choice == '5':
        pass
    else:
        print("❌ Некорректный выбор")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)