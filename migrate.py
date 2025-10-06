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


def migrate_up(manager: MigrationManager, target_version: int = None):
    """Применить миграции"""
    print("\n" + "=" * 60)
    print("Применение миграций")
    print("=" * 60)
    
    pending = manager.get_pending_migrations()
    
    if not pending:
        print("\n✅ База данных актуальна, миграции не требуются")
        return
    
    if target_version:
        pending = [(v, f) for v, f in pending if v <= target_version]
        print(f"\nЦелевая версия: {target_version}")
    else:
        print(f"\nБудет применено {len(pending)} миграций")
    
    for version, filename in pending:
        migration_name = filename.replace('.py', '').replace(f'{version:03d}_', '')
        print(f"  [{version}] {migration_name}")
    
    print()
    confirm = input("Продолжить? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("❌ Отменено")
        return
    
    success, total = manager.migrate(target_version)
    
    print("\n" + "=" * 60)
    if success == total:
        print(f"✅ Успешно применено {success} миграций")
    else:
        print(f"⚠️  Применено {success} из {total} миграций")
        print("Проверьте ошибки выше")
    print("=" * 60)


def show_status(manager: MigrationManager):
    """Показать статус миграций"""
    manager.print_status()


def create_new_migration(name: str):
    """Создать новую миграцию"""
    print("\n" + "=" * 60)
    print("Создание новой миграции")
    print("=" * 60)
    
    create_migration_template(name)
    
    print("\n" + "=" * 60)


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
        migrate_up(manager, args.target)
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
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)