#!/usr/bin/env python3
"""
Script for synchronizing subscriptions and fetching new videos.
"""

import sys
import os
from datetime import datetime

# Add the project root folder to the path
current_dir = os.path.dirname(os.path.abspath(__file__))  # src/
project_root = os.path.dirname(current_dir)  # project root
sys.path.insert(0, project_root)

from src.db_manager import Database
from src.youtube_api import YouTubeAPI
from locales.i18n import t, load_locale_from_config

# Load locale from settings
load_locale_from_config()


def sync_subscriptions(db: Database):
    """Synchronize subscriptions for all personal channels."""
    channels = db.get_all_personal_channels()

    if not channels:
        print(f"❌ {t('sync.no_channels')}")
        return

    print(t('sync.channels_found', count=len(channels)))

    for channel in channels:
        print(f"\n{'=' * 60}")
        print(t('sync.sync_channel', name=channel['name']))
        print('=' * 60)

        try:
            api = YouTubeAPI('config/client_secrets.json')
            api.authenticate(channel['oauth_token_path'])

            # Get subscriptions
            print(t('sync.loading_subscriptions'))
            subscriptions = api.get_subscriptions()
            print(t('sync.subscriptions_found', count=len(subscriptions)))

            # Get a list of YouTube channel IDs
            current_youtube_ids = [sub['channel_id'] for sub in subscriptions]

            # Synchronize status (active/inactive)
            print(t('sync.checking_status'))
            stats = db.sync_subscriptions_status(channel['id'], current_youtube_ids)

            if stats['deactivated'] > 0:
                print(f"  ⚠️  {t('sync.deactivated', count=stats['deactivated'])}")
            if stats['activated'] > 0:
                print(f"  ✓ {t('sync.activated', count=stats['activated'])}")
            print(f"  ✓ {t('sync.unchanged', count=stats['unchanged'])}")

            # Save new subscriptions to the database
            added_count = 0
            for sub in subscriptions:
                subscription_id = db.add_subscription(
                    personal_channel_id=channel['id'],
                    youtube_channel_id=sub['channel_id'],
                    channel_name=sub['channel_name'],
                    channel_thumbnail=sub['thumbnail']
                )
                if subscription_id:
                    added_count += 1

            if added_count > 0:
                print(f"  ✓ {t('sync.new_subscriptions', count=added_count)}")

            print(f"✓ {t('sync.sync_complete', channel=channel['name'])}")

        except Exception as e:
            print(f"❌ {t('common.error')}: {e}")
            continue


def sync_videos(db: Database, max_videos_per_channel: int = 5):
    """Fetch new videos from all subscriptions."""
    channels = db.get_all_personal_channels()
    
    if not channels:
        print(f"❌ {t('sync.no_channels')}")
        return

    total_new_videos = 0

    for channel in channels:
        print(f"\n{'=' * 60}")
        print(t('sync.video_loading', name=channel['name']))
        print('=' * 60)

        try:
            api = YouTubeAPI('config/client_secrets.json')
            api.authenticate(channel['oauth_token_path'])

            # Get subscriptions from the database
            subscriptions = db.get_subscriptions_by_channel(channel['id'])
            print(t('sync.processing_subscriptions', count=len(subscriptions)))

            channel_new_videos = 0
            
            for i, sub in enumerate(subscriptions, 1):
                try:
                    # Get the latest videos from the channel
                    videos = api.get_channel_videos(
                        sub['youtube_channel_id'],
                        max_results=max_videos_per_channel
                    )
                    
                    # Save to the database
                    for video in videos:
                        video_id = db.add_video(
                            subscription_id=sub['id'],
                            youtube_video_id=video['video_id'],
                            title=video['title'],
                            thumbnail=video['thumbnail'],
                            published_at=video['published_at'],
                            duration=video['duration'],
                            description=video.get('description'),
                            view_count=video.get('view_count')
                        )
                        
                        if video_id:  # New video
                            channel_new_videos += 1
                    
                    # Progress
                    if i % 10 == 0:
                        print(f"  {t('sync.progress', current=i, total=len(subscriptions))}")
                
                except Exception as e:
                    error_msg = str(e)
                    # Determine the error type
                    if 'playlistNotFound' in error_msg or '404' in error_msg:
                        error_type = 'PLAYLIST_NOT_FOUND'
                    elif 'duration' in error_msg:
                        error_type = 'DURATION_PARSE_ERROR'
                    elif 'quota' in error_msg.lower():
                        error_type = 'QUOTA_EXCEEDED'
                    else:
                        error_type = 'UNKNOWN'
                    
                    # Log the error
                    db.log_sync_error(
                        personal_channel_id=channel['id'],
                        subscription_id=sub['id'],
                        channel_name=sub['channel_name'],
                        error_type=error_type,
                        error_message=error_msg[:500]  # Limit the length
                    )
                    
                    print(f"  ⚠️  {t('sync.error_processing_subscription', channel=sub['channel_name'], error=error_type)}")
                    continue

            print(t('sync.new_videos_found', count=channel_new_videos, channel=channel['name']))
            total_new_videos += channel_new_videos

        except Exception as e:
            print(f"❌ {t('sync.error_processing_channel', error=str(e))}")
            continue

    print(f"\n{'=' * 60}")
    print(t('sync.sync_complete_global'))
    print(t('sync.total_new_videos', count=total_new_videos))

    # Show error statistics
    errors = db.get_unresolved_errors()
    if errors:
        print(f"\n⚠️  {t('sync.errors_found', count=len(errors))}")

        # Group by type
        error_types = {}
        for err in errors:
            error_types[err['error_type']] = error_types.get(err['error_type'], 0) + 1

        for error_type, count in error_types.items():
            print(f"  - {error_type}: {count} subscriptions")

        print(f"\n{t('sync.error_details')}")

    print('=' * 60)


def main():
    print("=" * 60)
    print(f"{t('app.name')} - {t('sync.title')}")
    print("=" * 60)

    db = Database()

    print(f"\n{t('sync.choose_action')}:")
    print("1. Synchronize subscriptions (update channel list)")
    print("2. Download new videos")
    print("3. Perform a full synchronization (subscriptions + videos)")

    choice = input(f"\n{t('sync.your_choice', min=1, max=3)}: ").strip()

    if choice == '1':
        sync_subscriptions(db)
    elif choice == '2':
        print("\nHow many videos to download from each channel?")
        try:
            max_videos = int(input(t('sync.video_count_default', default=5)).strip() or "5")
        except ValueError:
            max_videos = 5
        sync_videos(db, max_videos_per_channel=max_videos)
    elif choice == '3':
        sync_subscriptions(db)
        print(f"\n{'=' * 60}")
        print(t('sync.transition_to_videos'))
        print('=' * 60)
        sync_videos(db, max_videos_per_channel=5)
    else:
        print(f"❌ {t('sync.invalid_choice')}")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
