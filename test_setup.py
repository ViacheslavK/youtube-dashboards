#!/usr/bin/env python3
"""
Скрипт для проверки установки и настройки
"""

import os
import sys

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from locales.i18n import t, load_locale_from_config

# Загружаем локаль из настроек
load_locale_from_config()


def check_dependencies():
    """Проверка установленных зависимостей"""
    print(t('setup_check.checking_dependencies'))

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
        print(f"\n❌ {t('setup_check.missing_modules', modules=', '.join(missing))}")
        print(t('setup_check.install_dependencies'))
        return False

    print(t('setup_check.dependencies_ok'))
    return True


def check_structure():
    """Проверка структуры проекта"""
    print(t('setup_check.checking_structure'))

    required_dirs = [
        'config',
        'database',
    ]

    for directory in required_dirs:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"  ✓ {t('setup_check.creating_directory', directory=directory)}")
        else:
            print(f"  ✓ {directory}/")

    print(t('setup_check.structure_ok'))
    return True


def check_credentials():
    """Проверка наличия credentials"""
    print(t('setup_check.checking_credentials'))

    creds_file = 'config/client_secrets.json'

    if os.path.exists(creds_file):
        print(f"  ✓ {creds_file}")
        print(t('setup_check.credentials_ok'))
        return True
    else:
        print(f"  ✗ {t('setup_check.credentials_missing', file=creds_file)}")
        print(f"\n❌ {t('setup_check.instructions_title')}")
        print(f"\n{t('setup_check.oauth_steps')}")
        print(t('setup_check.oauth_project'))
        print(t('setup_check.oauth_api'))
        print(t('setup_check.oauth_credentials'))
        print(t('setup_check.oauth_download'))
        print(f"\n{t('setup_check.oauth_details')}")
        return False


def check_database():
    """Проверка базы данных"""
    print(t('setup_check.checking_database'))

    try:
        from src.db_manager import Database
        db = Database()

        channels = db.get_all_personal_channels()
        print(f"  ✓ {t('setup_check.db_initialized')}")
        print(f"  ℹ  {t('setup_check.channels_count', count=len(channels))}")

        if channels:
            print("\n  Личные каналы:")
            for ch in channels:
                videos_count = len(db.get_videos_by_personal_channel(ch['id']))
                print(t('setup_check.channel_videos', name=ch['name'], count=videos_count))

        print(t('setup_check.database_ok'))
        return True

    except Exception as e:
        print(f"  ✗ {t('setup_check.database_error', error=str(e))}")
        print(t('setup_check.database_problem'))
        return False


def main():
    print("=" * 60)
    print(t('setup_check.title'))
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
            print(f"❌ {t('setup_check.fix_errors')}'{name}': {e}\n")
            results.append(False)

    print("=" * 60)
    if all(results):
        print(t('setup_check.check_complete'))
        print(f"\n{t('setup_check.next_channels')}")
        print(t('setup_check.run_setup_channels'))
        print(t('setup_check.run_sync'))
    elif results[0] and results[1] and not results[2]:
        print(t('setup_check.almost_ready'))
        print(f"\n{t('setup_check.need_credentials')}")
        print(t('setup_check.see_readme'))
    elif results[0] and results[1] and results[2] and not results[3]:
        print(t('setup_check.credentials_ready'))
        print(f"\n{t('setup_check.run_setup')}")
    else:
        print(t('setup_check.fix_errors'))
        print(f"\n{t('setup_check.check_errors')}")

    print("=" * 60)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(0)
