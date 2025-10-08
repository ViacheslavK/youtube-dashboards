#!/usr/bin/env python3
"""
Скрипт для первоначальной настройки личных каналов
"""

import os
import sys

# Добавляем корневую папку проекта в путь
current_dir = os.path.dirname(os.path.abspath(__file__))  # src/
project_root = os.path.dirname(current_dir)  # корень проекта
sys.path.insert(0, project_root)

from src.db_manager import Database
from src.youtube_api import YouTubeAPI, setup_new_channel
from locales.i18n import t, load_locale_from_config

# Загружаем локаль из настроек
load_locale_from_config()


COLORS = [
    '#3b82f6',  # Blue
    '#ef4444',  # Red
    '#10b981',  # Green
    '#f59e0b',  # Amber
    '#8b5cf6',  # Purple
    '#ec4899',  # Pink
    '#06b6d4',  # Cyan
    '#84cc16',  # Lime
    '#f97316',  # Orange
    '#6366f1',  # Indigo
    '#14b8a6',  # Teal
    '#a855f7',  # Violet
]


def main():
    print("=" * 60)
    print(f"{t('app.name')} - {t('setup.title')}")
    print("=" * 60)

    # Проверяем наличие credentials
    credentials_file = 'config/client_secrets.json'
    if not os.path.exists(credentials_file):
        print(f"\n❌ {t('common.error').upper()}: client_secrets.json {t('app.not_found')}")
        print(f"\n{t('setup.instructions_title')}:")
        print("1. Зайти в Google Cloud Console: https://console.cloud.google.com/")
        print("2. Создать новый проект или выбрать существующий")
        print("3. Включить YouTube Data API v3")
        print("4. Создать OAuth 2.0 credentials (Desktop app)")
        print("5. Скачать JSON файл и сохранить как 'config/client_secrets.json'")
        print("\nПодробная инструкция: https://developers.google.com/youtube/v3/quickstart/python")
        sys.exit(1)
    
    # Создаём директории
    os.makedirs('config/youtube_credentials', exist_ok=True)
    os.makedirs('database', exist_ok=True)
    
    # Инициализируем БД
    db = Database()

    print(f"\n{t('setup.db_initialized')}")

    # Проверяем существующие каналы
    existing_channels = db.get_all_personal_channels()
    if existing_channels:
        print(f"\n📺 {t('setup.channels_found', count=len(existing_channels))}")
        for ch in existing_channels:
            print(f"  - {ch['name']} (ID: {ch['id']})")

        print(f"\n{t('setup.choose_action')}:")
        print("1. Добавить новый канал")
        print("2. Обновить существующие каналы")
        print("3. Выход")

        choice = input(f"\n{t('setup.your_choice', min=1, max=3)}: ").strip()
        
        if choice == '3':
            sys.exit(0)
        elif choice == '2':
            update_existing_channels(db, existing_channels)
            return
    
    # Добавление новых каналов
    add_new_channels(db)


def add_new_channels(db: Database):
    """Добавление новых личных каналов"""
    print(f"\n{'=' * 60}")
    print(t('setup.adding_channels_title'))
    print('=' * 60)

    print(f"\n{t('setup.channels_count')}")
    print("(У вас 12 каналов, но активно используете 7)")

    try:
        count = int(input(t('setup.channels_input')).strip())
    except ValueError:
        print(f"❌ {t('setup.invalid_count')}")
        return

    if count <= 0 or count > 20:
        print(f"❌ {t('setup.invalid_range')}")
        return
    
    channels_data = []
    
    for i in range(count):
        print(f"\n{'=' * 60}")
        print(f"{t('setup.channel_progress', current=i+1, total=count)}")
        print('=' * 60)

        name = input(f"{t('setup.channel_name')}: ").strip()
        if not name:
            print(f"❌ {t('setup.name_required')}")
            continue

        # Выбираем цвет
        color = COLORS[i % len(COLORS)]
        print(f"{t('setup.channel_color', color=color)}")

        try:
            # Авторизация через OAuth
            channel_info = setup_new_channel(name, 'config/client_secrets.json')
            channel_info['color'] = color
            channels_data.append(channel_info)

        except Exception as e:
            print(f"❌ {t('setup.auth_error', error=str(e))}")
            print(t('setup.skip_channel'))
            continue
    
    # Сохраняем в БД
    if channels_data:
        print(f"\n{'=' * 60}")
        print(t('setup.saving_channels_title'))
        print('=' * 60)

        for i, ch_data in enumerate(channels_data, 1):
            channel_id = db.add_personal_channel(
                name=ch_data['name'],
                youtube_channel_id=ch_data['youtube_channel_id'],
                oauth_token_path=ch_data['token_file'],
                color=ch_data['color'],
                order_position=i
            )
            print(f"✓ {t('setup.channel_added', name=ch_data['name'], id=channel_id)}")

        print(f"\n✅ {t('setup.all_channels_setup')}")
        print(f"\n{t('setup.run_sync_hint')}")
    else:
        print(f"\n⚠️  {t('setup.setup_incomplete')}")


def update_existing_channels(db: Database, channels: list):
    """Обновление подписок для существующих каналов"""
    print(f"\n{'=' * 60}")
    print(t('setup.update_channels_title'))
    print('=' * 60)

    for channel in channels:
        print(f"\n--- {t('setup.updating_channel', name=channel['name'])} ---")

        try:
            api = YouTubeAPI('config/client_secrets.json')
            api.authenticate(channel['oauth_token_path'])

            print(f"✓ {t('setup.auth_success_general')}")

            # Получаем подписки
            print(t('setup.loading_subs'))
            subscriptions = api.get_subscriptions()
            print(t('setup.subs_found', count=len(subscriptions)))

            # Сохраняем в БД
            for sub in subscriptions:
                db.add_subscription(
                    personal_channel_id=channel['id'],
                    youtube_channel_id=sub['channel_id'],
                    channel_name=sub['channel_name'],
                    channel_thumbnail=sub['thumbnail']
                )

            print(t('setup.subs_updated', channel=channel['name']))

        except Exception as e:
            print(f"❌ {t('setup.update_error', name=channel['name'], error=str(e))}")
            continue

    print(f"\n✅ {t('setup.update_complete')}")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
