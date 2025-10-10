#!/usr/bin/env python3
"""
Subscription management (view inactive, delete from history)
"""

import sys
import os
from datetime import datetime

# Add project root folder to path
current_dir = os.path.dirname(os.path.abspath(__file__))  # utils/
project_root = os.path.dirname(current_dir)  # project root
sys.path.insert(0, project_root)

from src.db_manager import Database
from locales import t, load_locale_from_config

# Load locale from settings
load_locale_from_config()


def view_inactive_subscriptions():
    """Show inactive subscriptions"""
    db = Database()
    channels = db.get_all_personal_channels()

    print(f"\n{'=' * 80}")
    print(t('subscriptions.inactive_title'))
    print('=' * 80)

    total_inactive = 0

    for channel in channels:
        # Get only inactive ones
        all_subs = db.get_subscriptions_by_channel(channel['id'], include_inactive=True)
        inactive_subs = [s for s in all_subs if not s['is_active']]

        if inactive_subs:
            print(f"\n📺 {t('subscriptions.inactive_per_channel', name=channel['name'], count=len(inactive_subs))}")

            for sub in inactive_subs:
                deactivated = datetime.fromisoformat(sub['deactivated_at']) if sub['deactivated_at'] else None
                time_str = deactivated.strftime('%Y-%m-%d') if deactivated else t('common.unknown')
                print(f"   {t('subscriptions.subscription_info', id=sub['id'], name=sub['channel_name'], date=time_str)}")

            total_inactive += len(inactive_subs)

    if total_inactive == 0:
        print(f"\n{t('subscriptions.no_inactive')}")
    else:
        print(f"\n{'=' * 80}")
        print(t('subscriptions.total_inactive', count=total_inactive))
        print(f"\n{t('subscriptions.delete_hint')}")
        print('=' * 80)


def delete_inactive_interactive():
    """Interactive deletion of inactive subscriptions"""
    db = Database()
    channels = db.get_all_personal_channels()

    print(f"\n{'=' * 80}")
    print(t('subscriptions.delete_title'))
    print('=' * 80)

    for channel in channels:
        all_subs = db.get_subscriptions_by_channel(channel['id'], include_inactive=True)
        inactive_subs = [s for s in all_subs if not s['is_active']]

        if not inactive_subs:
            continue

        print(f"\n📺 {channel['name']}: {len(inactive_subs)} {t('subscriptions.inactive')}")

        for sub in inactive_subs:
            print(t('subscriptions.processing_channel', name=sub['channel_name'], id=sub['id']))

            choice = input(t('subscriptions.delete_prompt')).strip().lower()

            if choice == 'q':
                print(t('subscriptions.user_cancelled'))
                return
            elif choice == 'y':
                db.mark_subscription_deleted(sub['id'])
                print(t('subscriptions.deleted'))
            else:
                print(t('subscriptions.skipped'))

    print(f"\n{'=' * 80}")
    print(t('subscriptions.delete_complete'))
    print('=' * 80)


def delete_all_inactive():
    """Delete all inactive subscriptions"""
    db = Database()
    channels = db.get_all_personal_channels()

    total = 0

    for channel in channels:
        all_subs = db.get_subscriptions_by_channel(channel['id'], include_inactive=True)
        inactive_subs = [s for s in all_subs if not s['is_active']]

        for sub in inactive_subs:
            db.mark_subscription_deleted(sub['id'])
            total += 1

    print(t('subscriptions.delete_all_count', count=total))


def view_statistics():
    """Subscription statistics"""
    db = Database()
    channels = db.get_all_personal_channels()

    print(f"\n{'=' * 80}")
    print(t('subscriptions.stats_title'))
    print('=' * 80)

    total_active = 0
    total_inactive = 0
    total_deleted = 0

    for channel in channels:
        all_subs = db.get_subscriptions_by_channel(channel['id'], include_inactive=True)

        active = len([s for s in all_subs if s['is_active']])
        inactive = len([s for s in all_subs if not s['is_active']])

        # Count deleted ones (requires separate query)
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) as count FROM subscriptions
            WHERE personal_channel_id = ? AND deleted_by_user = 1
        ''', (channel['id'],))
        deleted = cursor.fetchone()['count']
        conn.close()

        print(f"\n📺 {t('subscriptions.channel_stats', name=channel['name'])}")
        print(t('subscriptions.stats_active', count=active))
        print(t('subscriptions.stats_inactive', count=inactive))
        print(t('subscriptions.stats_deleted', count=deleted))

        total_active += active
        total_inactive += inactive
        total_deleted += deleted

    print(f"\n{'=' * 80}")
    print(t('subscriptions.stats_total'))
    print(t('subscriptions.stats_active', count=total_active))
    print(t('subscriptions.stats_inactive', count=total_inactive))
    print(t('subscriptions.stats_deleted', count=total_deleted))
    print('=' * 80)


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == '--delete-inactive':
            delete_all_inactive()
            return

    print("=" * 80)
    print(t('menu_subscriptions.title'))
    print("=" * 80)

    print(f"\n{t('menu_subscriptions.choose_action')}")
    print(f"1. {t('menu_subscriptions.view_inactive')}")
    print(f"2. {t('menu_subscriptions.delete_interactive')}")
    print(f"3. {t('menu_subscriptions.delete_all')}")
    print(f"4. {t('menu_subscriptions.statistics')}")
    print(f"5. {t('menu.exit')}")

    choice = input(f"\n{t('menu.your_choice', min=1, max=5)} ").strip()

    if choice == '1':
        view_inactive_subscriptions()
    elif choice == '2':
        delete_inactive_interactive()
    elif choice == '3':
        confirm = input(f"\n{t('subscriptions.delete_all_confirm')} ").strip().lower()
        if confirm == 'yes':
            delete_all_inactive()
        else:
            print(t('subscriptions.delete_cancelled'))
    elif choice == '4':
        view_statistics()
    elif choice == '5':
        pass
    else:
        print(t('menu.invalid_choice'))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
