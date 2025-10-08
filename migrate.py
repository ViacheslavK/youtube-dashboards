#!/usr/bin/env python3
"""
CLI для управления миграциями базы данных
"""

import sys
import os
import argparse

# Добавляем путь к migrations
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from migrations.migration_manager import MigrationManager, create_migration_template
from locales.i18n import t, load_locale_from_config

# Загружаем локаль из настроек
load_locale_from_config()


def migrate_up(manager: MigrationManager, target_version: int = None, auto_yes: bool = False):
    """Применить миграции"""
    print(f"\n{'=' * 60}")
    print(t('migrations.apply_migrations'))
    print('=' * 60)

    pending = manager.get_pending_migrations()

    if not pending:
        print(f"\n✅ {t('migrations.up_to_date')}")
        return

    if target_version:
        pending = [(v, f) for v, f in pending if v <= target_version]
        print(f"\n{t('migrations.target_version', version=target_version)}")
    else:
        print(f"\n{t('migrations.will_apply', count=len(pending))}")

    for version, filename in pending:
        migration_name = filename.replace('.py', '').replace(f'{version:03d}_', '')
        print(f"  [{version}] {migration_name}")

    if not auto_yes:
        print()
        confirm = input(f"{t('migrations.confirm')}: ").strip().lower()

        if confirm != 'yes':
            print(f"❌ {t('migrations.cancelled')}")
            return
    else:
        print(f"\n{t('migrations.auto_confirm')}")

    success, total = manager.migrate(target_version)

    print(f"\n{'=' * 60}")
    if success == total:
        print(f"✅ {t('migrations.success', count=success)}")
    else:
        print(f"⚠️  {t('migrations.partial', success=success, total=total)}")
        print(t('migrations.check_errors'))
    print('=' * 60)


def show_status(manager: MigrationManager):
    """Показать статус миграций"""
    manager.print_status()


def create_new_migration(name: str):
    """Создать новую миграцию"""
    print(f"\n{'=' * 60}")
    print(t('migrations.creating_migration'))
    print('=' * 60)

    create_migration_template(name)

    print(f"\n{'=' * 60}")


def main():
    parser = argparse.ArgumentParser(
        description='Управление миграциями базы данных YouTube Dashboard'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Команды')
    
    # migrate up
    migrate_parser = subparsers.add_parser('up', help='Применить миграции')
    migrate_parser.add_argument(
        '--target', 
        type=int, 
        help='Целевая версия (по умолчанию - последняя)'
    )
    migrate_parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='Автоматически подтвердить (для CI/CD)'
    )
    
    # status
    subparsers.add_parser('status', help='Показать статус миграций')
    
    # create
    create_parser = subparsers.add_parser('create', help='Создать новую миграцию')
    create_parser.add_argument('name', help='Название миграции (например, add_user_settings)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Инициализируем менеджер
    manager = MigrationManager()
    
    if args.command == 'up':
        migrate_up(manager, args.target, args.yes)
    elif args.command == 'status':
        show_status(manager)
    elif args.command == 'create':
        create_new_migration(args.name)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ {t('common.error')}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
