#!/usr/bin/env python3
"""
Просмотр ошибок синхронизации
"""

import sys
import os
from datetime import datetime

# Добавляем корневую папку проекта в путь
current_dir = os.path.dirname(os.path.abspath(__file__))  # utils/
project_root = os.path.dirname(current_dir)  # корень проекта
sys.path.insert(0, project_root)

from src.db_manager import Database
from locales import t, load_locale_from_config

# Загружаем локаль из настроек
load_locale_from_config()


def view_errors():
    """Показать все нерешённые ошибки"""
    db = Database()

    errors = db.get_unresolved_errors()

    if not errors:
        print(t('errors.no_errors'))
        return

    print(f"\n{'=' * 80}")
    print(t('errors.found_errors', count=len(errors)))
    print('=' * 80)
    
    # Группируем по типу
    error_types = {}
    for err in errors:
        if err['error_type'] not in error_types:
            error_types[err['error_type']] = []
        error_types[err['error_type']].append(err)
    
    # Выводим по группам
    for error_type, errs in error_types.items():
        print(f"\n{'─' * 80}")
        print(t('errors.errors_by_type', type=error_type, count=len(errs)))
        print('─' * 80)

        for err in errs[:10]:  # Показываем первые 10
            occurred = datetime.fromisoformat(err['occurred_at'])
            print(f"\n{t('errors.id', id=err['id'])}")
            print(t('errors.channel', name=err['channel_name']))
            print(t('errors.occurred_at', date=occurred.strftime('%Y-%m-%d %H:%M:%S')))

            # Показываем короткое сообщение
            msg = err['error_message']
            if len(msg) > 100:
                msg = msg[:100] + "..."
            print(t('errors.message', msg=msg))

        if len(errs) > 10:
            print(f"\n{t('errors.more_errors', count=len(errs) - 10)}")

    print(f"\n{'=' * 80}")


def view_errors_by_channel():
    """Показать ошибки по каналам"""
    db = Database()

    channels = db.get_all_personal_channels()

    print(f"\n{'=' * 80}")
    print(t('errors.by_channel_title'))
    print('=' * 80)

    total_errors = 0

    for channel in channels:
        errors = db.get_unresolved_errors(channel['id'])

        if errors:
            print(f"\n📺 {t('errors.channel_errors', channel=channel['name'], count=len(errors))}")

            # Группируем по типу
            error_types = {}
            for err in errors:
                error_types[err['error_type']] = error_types.get(err['error_type'], 0) + 1

            for error_type, count in error_types.items():
                print(t('errors.error_types', type=error_type, count=count))

            total_errors += len(errors)

    if total_errors == 0:
        print(t('errors.no_errors'))
    else:
        print(f"\n{'=' * 80}")
        print(t('errors.total_unresolved', count=total_errors))
        print('=' * 80)


def explain_errors():
    """Объяснение типов ошибок"""
    print(f"\n{'=' * 80}")
    print(t('errors.explanations_title'))
    print('=' * 80)

    print(f"\n{t('errors.playlist_not_found')}")
    print(f"\n{t('errors.duration_parse_error')}")
    print(f"\n{t('errors.quota_exceeded')}")
    print(f"\n{t('errors.unknown')}")

    print(f"\n{'=' * 80}")


def main():
    print("=" * 80)
    print(t('menu_errors.title'))
    print("=" * 80)

    print(f"\n{t('menu_errors.choose_action')}")
    print(f"1. {t('menu_errors.show_all')}")
    print(f"2. {t('menu_errors.by_channel')}")
    print(f"3. {t('menu_errors.explanations')}")
    print(f"4. {t('menu.exit')}")

    choice = input(f"\n{t('menu.your_choice', min=1, max=4)} ").strip()

    if choice == '1':
        view_errors()
    elif choice == '2':
        view_errors_by_channel()
    elif choice == '3':
        explain_errors()
    elif choice == '4':
        pass
    else:
        print(t('menu.invalid_choice'))


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
