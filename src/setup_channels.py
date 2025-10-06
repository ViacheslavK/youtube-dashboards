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
    print("YouTube Dashboard - Настройка личных каналов")
    print("=" * 60)
    
    # Проверяем наличие credentials
    credentials_file = 'config/client_secrets.json'
    if not os.path.exists(credentials_file):
        print("\n❌ ОШИБКА: Файл client_secrets.json не найден!")
        print("\nДля начала работы необходимо:")
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
    
    print("\nБаза данных инициализирована.")
    
    # Проверяем существующие каналы
    existing_channels = db.get_all_personal_channels()
    if existing_channels:
        print(f"\n📺 Найдено {len(existing_channels)} настроенных каналов:")
        for ch in existing_channels:
            print(f"  - {ch['name']} (ID: {ch['id']})")
        
        print("\nВыберите действие:")
        print("1. Добавить новый канал")
        print("2. Обновить существующие каналы")
        print("3. Выход")
        
        choice = input("\nВаш выбор (1-3): ").strip()
        
        if choice == '3':
            sys.exit(0)
        elif choice == '2':
            update_existing_channels(db, existing_channels)
            return
    
    # Добавление новых каналов
    add_new_channels(db)


def add_new_channels(db: Database):
    """Добавление новых личных каналов"""
    print("\n" + "=" * 60)
    print("Добавление новых личных каналов")
    print("=" * 60)
    
    print("\nСколько личных каналов вы хотите добавить?")
    print("(У вас 12 каналов, но активно используете 7)")
    
    try:
        count = int(input("Количество каналов: ").strip())
    except ValueError:
        print("❌ Некорректное число")
        return
    
    if count <= 0 or count > 20:
        print("❌ Количество должно быть от 1 до 20")
        return
    
    channels_data = []
    
    for i in range(count):
        print(f"\n{'=' * 60}")
        print(f"Канал {i + 1} из {count}")
        print('=' * 60)
        
        name = input(f"Название канала (например, 'Технологии', 'Музыка'): ").strip()
        if not name:
            print("❌ Название не может быть пустым. Пропускаем...")
            continue
        
        # Выбираем цвет
        color = COLORS[i % len(COLORS)]
        print(f"Цвет для канала: {color}")
        
        try:
            # Авторизация через OAuth
            channel_info = setup_new_channel(name, 'config/client_secrets.json')
            channel_info['color'] = color
            channels_data.append(channel_info)
            
        except Exception as e:
            print(f"❌ Ошибка при настройке канала: {e}")
            print("Пропускаем этот канал...")
            continue
    
    # Сохраняем в БД
    if channels_data:
        print(f"\n{'=' * 60}")
        print("Сохранение каналов в базу данных...")
        print('=' * 60)
        
        for i, ch_data in enumerate(channels_data, 1):
            channel_id = db.add_personal_channel(
                name=ch_data['name'],
                youtube_channel_id=ch_data['youtube_channel_id'],
                oauth_token_path=ch_data['token_file'],
                color=ch_data['color'],
                order_position=i
            )
            print(f"✓ Канал '{ch_data['name']}' добавлен (ID: {channel_id})")
        
        print("\n✅ Все каналы успешно настроены!")
        print("\nТеперь можно загрузить подписки. Запустите:")
        print("  python sync_subscriptions.py")
    else:
        print("\n⚠️  Ни один канал не был добавлен.")


def update_existing_channels(db: Database, channels: list):
    """Обновление подписок для существующих каналов"""
    print("\n" + "=" * 60)
    print("Обновление подписок для существующих каналов")
    print("=" * 60)
    
    for channel in channels:
        print(f"\n--- Обновление: {channel['name']} ---")
        
        try:
            api = YouTubeAPI('config/client_secrets.json')
            api.authenticate(channel['oauth_token_path'])
            
            print("✓ Авторизация успешна")
            
            # Получаем подписки
            print("Загрузка подписок...")
            subscriptions = api.get_subscriptions()
            print(f"Найдено {len(subscriptions)} подписок")
            
            # Сохраняем в БД
            for sub in subscriptions:
                db.add_subscription(
                    personal_channel_id=channel['id'],
                    youtube_channel_id=sub['channel_id'],
                    channel_name=sub['channel_name'],
                    channel_thumbnail=sub['thumbnail']
                )
            
            print(f"✓ Подписки обновлены для '{channel['name']}'")
            
        except Exception as e:
            print(f"❌ Ошибка при обновлении канала '{channel['name']}': {e}")
            continue
    
    print("\n✅ Обновление завершено!")


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