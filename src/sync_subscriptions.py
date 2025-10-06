#!/usr/bin/env python3
"""
Скрипт для синхронизации подписок и получения новых видео
"""

import sys
import os
from datetime import datetime

# Добавляем корневую папку проекта в путь
current_dir = os.path.dirname(os.path.abspath(__file__))  # src/
project_root = os.path.dirname(current_dir)  # корень проекта
sys.path.insert(0, project_root)

from src.db_manager import Database
from src.youtube_api import YouTubeAPI


def sync_subscriptions(db: Database):
    """Синхронизация подписок для всех личных каналов"""
    channels = db.get_all_personal_channels()
    
    if not channels:
        print("❌ Нет настроенных каналов. Запустите setup_channels.py")
        return
    
    print(f"Найдено {len(channels)} личных каналов")
    
    for channel in channels:
        print(f"\n{'=' * 60}")
        print(f"Синхронизация: {channel['name']}")
        print('=' * 60)
        
        try:
            api = YouTubeAPI('config/client_secrets.json')
            api.authenticate(channel['oauth_token_path'])
            
            # Получаем подписки
            print("Загрузка подписок с YouTube...")
            subscriptions = api.get_subscriptions()
            print(f"Найдено {len(subscriptions)} подписок на YouTube")
            
            # Получаем список YouTube channel IDs
            current_youtube_ids = [sub['channel_id'] for sub in subscriptions]
            
            # Синхронизируем статус (активные/неактивные)
            print("Проверка статуса подписок...")
            stats = db.sync_subscriptions_status(channel['id'], current_youtube_ids)
            
            if stats['deactivated'] > 0:
                print(f"  ⚠️  Деактивировано: {stats['deactivated']} (отписались)")
            if stats['activated'] > 0:
                print(f"  ✓ Реактивировано: {stats['activated']} (переподписались)")
            print(f"  ✓ Без изменений: {stats['unchanged']}")
            
            # Сохраняем новые подписки в БД
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
                print(f"  ✓ Добавлено новых подписок: {added_count}")
            
            print(f"✓ Синхронизация '{channel['name']}' завершена")
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            continue


def sync_videos(db: Database, max_videos_per_channel: int = 5):
    """Получение новых видео со всех подписок"""
    channels = db.get_all_personal_channels()
    
    if not channels:
        print("❌ Нет настроенных каналов")
        return
    
    total_new_videos = 0
    
    for channel in channels:
        print(f"\n{'=' * 60}")
        print(f"Загрузка видео: {channel['name']}")
        print('=' * 60)
        
        try:
            api = YouTubeAPI('config/client_secrets.json')
            api.authenticate(channel['oauth_token_path'])
            
            # Получаем подписки из БД
            subscriptions = db.get_subscriptions_by_channel(channel['id'])
            print(f"Обработка {len(subscriptions)} подписок...")
            
            channel_new_videos = 0
            
            for i, sub in enumerate(subscriptions, 1):
                try:
                    # Получаем последние видео с канала
                    videos = api.get_channel_videos(
                        sub['youtube_channel_id'],
                        max_results=max_videos_per_channel
                    )
                    
                    # Сохраняем в БД
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
                        
                        if video_id:  # Новое видео
                            channel_new_videos += 1
                    
                    # Прогресс
                    if i % 10 == 0:
                        print(f"  Обработано {i}/{len(subscriptions)} подписок...")
                
                except Exception as e:
                    error_msg = str(e)
                    # Определяем тип ошибки
                    if 'playlistNotFound' in error_msg or '404' in error_msg:
                        error_type = 'PLAYLIST_NOT_FOUND'
                    elif 'duration' in error_msg:
                        error_type = 'DURATION_PARSE_ERROR'
                    elif 'quota' in error_msg.lower():
                        error_type = 'QUOTA_EXCEEDED'
                    else:
                        error_type = 'UNKNOWN'
                    
                    # Логируем ошибку
                    db.log_sync_error(
                        personal_channel_id=channel['id'],
                        subscription_id=sub['id'],
                        channel_name=sub['channel_name'],
                        error_type=error_type,
                        error_message=error_msg[:500]  # Ограничиваем длину
                    )
                    
                    print(f"  ⚠️  Ошибка при обработке подписки '{sub['channel_name']}': {error_type}")
                    continue
            
            print(f"✓ Найдено {channel_new_videos} новых видео для '{channel['name']}'")
            total_new_videos += channel_new_videos
            
        except Exception as e:
            print(f"❌ Ошибка при обработке канала: {e}")
            continue
    
    print(f"\n{'=' * 60}")
    print(f"✅ Синхронизация завершена!")
    print(f"Всего новых видео: {total_new_videos}")
    
    # Показываем статистику ошибок
    errors = db.get_unresolved_errors()
    if errors:
        print(f"\n⚠️  Обнаружено {len(errors)} ошибок при синхронизации:")
        
        # Группируем по типу
        error_types = {}
        for err in errors:
            error_types[err['error_type']] = error_types.get(err['error_type'], 0) + 1
        
        for error_type, count in error_types.items():
            print(f"  - {error_type}: {count} подписок")
        
        print("\nПодробности можно посмотреть в админ-панели (после запуска веб-интерфейса)")
    
    print('=' * 60)


def main():
    print("=" * 60)
    print("YouTube Dashboard - Синхронизация")
    print("=" * 60)
    
    db = Database()
    
    print("\nВыберите действие:")
    print("1. Синхронизировать подписки (обновить список каналов)")
    print("2. Загрузить новые видео")
    print("3. Выполнить полную синхронизацию (подписки + видео)")
    
    choice = input("\nВаш выбор (1-3): ").strip()
    
    if choice == '1':
        sync_subscriptions(db)
    elif choice == '2':
        print("\nСколько видео загружать с каждого канала?")
        try:
            max_videos = int(input("Количество (по умолчанию 5): ").strip() or "5")
        except ValueError:
            max_videos = 5
        sync_videos(db, max_videos_per_channel=max_videos)
    elif choice == '3':
        sync_subscriptions(db)
        print("\n" + "=" * 60)
        print("Переход к загрузке видео...")
        print("=" * 60)
        sync_videos(db, max_videos_per_channel=5)
    else:
        print("❌ Некорректный выбор")


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