#!/usr/bin/env python3
"""
View statistics for loaded data
"""

import os
import sys

# Add project root to path
# __file__ = D:\...\utils\view_stats.py
current_dir = os.path.dirname(os.path.abspath(__file__))  # utils/
project_root = os.path.dirname(current_dir)  # project root
sys.path.insert(0, project_root)

from src.db_manager import Database
from locales.i18n import t, load_locale_from_config

# Load locale from settings
load_locale_from_config()


def view_channels_stats():
    """Channel statistics"""
    db = Database()
    
    channels = db.get_all_personal_channels()
    print(f"\n{'=' * 80}")
    print(t('channels.count', count=len(channels)))
    print('=' * 80)
    
    if not channels:
        print(f"\n⚠️  {t('channels.no_channels')}")
        print(t('channels.setup_prompt'))
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
        print(t('channels.translated_channel_color', color=ch['color']))
        print(t('channels.translated_subscriptions', count=len(subs)))
        print(t('channels.translated_videos', total=len(videos), unviewed=len(unwatched)))

        if ch['authuser_index'] is not None:
            print(t('channels.authuser_index', index=ch['authuser_index']))
        
        total_videos += len(videos)
        total_subscriptions += len(subs)
        total_unwatched += len(unwatched)
    
    print(f"\n{'=' * 80}")
    print(t('stats.title').upper())
    print(f"   {t('stats.total_subscriptions', count=total_subscriptions)}")
    print(f"   {t('stats.total_videos', count=total_videos)}")
    print(f"   {t('stats.unwatched_videos', count=total_unwatched)}")
    print('=' * 80)


def view_recent_videos(limit: int = 20):
    """Show recent videos"""
    db = Database()
    channels = db.get_all_personal_channels()

    if not channels:
        print(f"\n⚠️  {t('channels.no_channels')}")
        return

    print(f"\n{'=' * 80}")
    print(t('videos.recent_videos', count=limit))
    print('=' * 80)

    all_videos = []
    for ch in channels:
        videos = db.get_videos_by_personal_channel(ch['id'], include_watched=True)
        for v in videos:
            v['personal_channel_name'] = ch['name']
        all_videos.extend(videos)

    # Sort by publication date
    all_videos.sort(key=lambda x: x['published_at'], reverse=True)
    
    for v in all_videos[:limit]:
        watched = "✓" if v['is_watched'] else "📹"
        print(f"\n{watched} [{v['personal_channel_name']}] {v['title']}")
        print(t('videos.channel', channel=v['channel_name']))
        print(t('videos.published_duration', date=v['published_at'][:10], duration=v['duration']))


def view_subscriptions():
    """Show all subscriptions"""
    db = Database()
    channels = db.get_all_personal_channels()

    print(f"\n{'=' * 80}")
    print(t('subscriptions.title'))
    print('=' * 80)

    for ch in channels:
        subs = db.get_subscriptions_by_channel(ch['id'], include_inactive=False)

        if subs:
            print(f"\n📺 {ch['name']}: {len(subs)} {t('subscriptions.active')}")
            for i, sub in enumerate(subs[:10], 1):
                print(f"   {i}. {sub['channel_name']}")

            if len(subs) > 10:
                print(f"   ... {t('subscriptions.more_subs', count=len(subs) - 10)}")


def main():
    print("=" * 80)
    print(t('stats.title'))
    print("=" * 80)
    
    print(f"\n{t('menu.choose_action')}")
    print(f"1. {t('stats.title')} - по каналам")
    print(f"2. {t('videos.recent_videos', count=20)}")
    print(f"3. {t('videos.recent_videos', count=50)}")
    print(f"4. {t('subscriptions.title')} - список")
    print(f"5. {t('menu.exit')}")
    
    choice = input(f"\n{t('menu.your_choice', min=1, max=5)} ").strip()
    
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
