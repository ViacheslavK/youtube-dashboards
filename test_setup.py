#!/usr/bin/env python3
"""
Скрипт для проверки установки и настройки
"""

import os
import sys


def check_dependencies():
    """Проверка установленных зависимостей"""
    print("Проверка зависимостей...")
    
    required = [
        'google.auth',
        'googleapiclient',
        'isodate',
        'flask',
    ]
    
    missing = []
    for module in required:
        try:
            __import__(module)
            print(f"  ✓ {module}")
        except ImportError:
            print(f"  ✗ {module}")
            missing.append(module)
    
    if missing:
        print(f"\n❌ Отсутствуют модули: {', '.join(missing)}")
        print("Запустите: pip install -r requirements.txt")
        return False
    
    print("✅ Все зависимости установлены\n")
    return True


def check_structure():
    """Проверка структуры проекта"""
    print("Проверка структуры проекта...")
    
    required_dirs = [
        'config',
        'database',
    ]
    
    for directory in required_dirs:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"  ✓ Создана папка: {directory}")
        else:
            print(f"  ✓ {directory}/")
    
    print("✅ Структура проекта готова\n")
    return True


def check_credentials():
    """Проверка наличия credentials"""
    print("Проверка credentials...")
    
    creds_file = 'config/client_secrets.json'
    
    if os.path.exists(creds_file):
        print(f"  ✓ {creds_file}")
        print("✅ Credentials найдены\n")
        return True
    else:
        print(f"  ✗ {creds_file} не найден")
        print("\n❌ Необходимо создать OAuth credentials")
        print("\nИнструкция:")
        print("1. Зайдите в https://console.cloud.google.com/")
        print("2. Создайте проект")
        print("3. Включите YouTube Data API v3")
        print("4. Создайте OAuth 2.0 credentials (Desktop app)")
        print("5. Скачайте JSON и сохраните как config/client_secrets.json")
        print("\nПодробнее в README.md\n")
        return False


def check_database():
    """Проверка базы данных"""
    print("Проверка базы данных...")
    
    try:
        from src.db_manager import Database
        db = Database()
        
        channels = db.get_all_personal_channels()
        print(f"  ✓ База данных инициализирована")
        print(f"  ℹ  Настроено каналов: {len(channels)}")
        
        if channels:
            print("\n  Личные каналы:")
            for ch in channels:
                videos_count = len(db.get_videos_by_personal_channel(ch['id']))
                print(f"    - {ch['name']}: {videos_count} видео")
        
        print("✅ База данных работает\n")
        return True
        
    except Exception as e:
        print(f"  ✗ Ошибка: {e}")
        print("❌ Проблема с базой данных\n")
        return False


def main():
    print("=" * 60)
    print("YouTube Dashboard - Проверка установки")
    print("=" * 60)
    print()
    
    checks = [
        ("Зависимости", check_dependencies),
        ("Структура проекта", check_structure),
        ("Credentials", check_credentials),
        ("База данных", check_database),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Ошибка при проверке '{name}': {e}\n")
            results.append(False)
    
    print("=" * 60)
    if all(results):
        print("✅ Всё готово к работе!")
        print("\nСледующие шаги:")
        print("1. python setup_channels.py  - Настроить личные каналы")
        print("2. python sync_subscriptions.py  - Загрузить видео")
    elif results[0] and results[1] and not results[2]:
        print("⚠️  Почти готово!")
        print("\nНеобходимо создать OAuth credentials:")
        print("См. инструкцию в README.md")
    elif results[0] and results[1] and results[2] and not results[3]:
        print("⚠️  Credentials готовы, но каналы не настроены")
        print("\nЗапустите: python setup_channels.py")
    else:
        print("❌ Необходимо исправить ошибки")
        print("\nСм. сообщения выше")
    
    print("=" * 60)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(0)