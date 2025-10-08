#!/usr/bin/env python3
"""
Управление подписками (просмотр неактивных, удаление из истории)
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


def view_inactive_subscriptions():
    """Показать неактивные подписки"""
    db = Database()
    channels = db.get_all_personal_channels()
    
    print(f"\n{'=' * 80}")
    print("Неактивные подписки (от которых вы отписались)")
    print('=' * 80)
    
    total_inactive = 0
    
    for channel in channels:
        # Получаем только неактивные
        all_subs = db.get_subscriptions_by_channel(channel['id'], include_inactive=True)
        inactive_subs = [s for s in all_subs if not s['is_active']]
        
        if inactive_subs:
            print(f"\n📺 {channel['name']}: {len(inactive_subs)} неактивных")
            
            for sub in inactive_subs:
                deactivated = datetime.fromisoformat(sub['deactivated_at']) if sub['deactivated_at'] else None
                time_str = deactivated.strftime('%Y-%m-%d') if deactivated else 'неизвестно'
                print(f"   [{sub['id']}] {sub['channel_name']} (с {time_str})")
            
            total_inactive += len(inactive_subs)
    
    if total_inactive == 0:
        print("\n✅ Нет неактивных подписок!")
    else:
        print(f"\n{'=' * 80}")
        print(f"Всего неактивных подписок: {total_inactive}")
        print("\nЧтобы удалить из истории: python manage_subscriptions.py --delete-inactive")
        print('=' * 80)


def delete_inactive_interactive():
    """Интерактивное удаление неактивных подписок"""
    db = Database()
    channels = db.get_all_personal_channels()
    
    print(f"\n{'=' * 80}")
    print("Удаление неактивных подписок из истории")
    print('=' * 80)
    
    for channel in channels:
        all_subs = db.get_subscriptions_by_channel(channel['id'], include_inactive=True)
        inactive_subs = [s for s in all_subs if not s['is_active']]
        
        if not inactive_subs:
            continue
        
        print(f"\n📺 {channel['name']}: {len(inactive_subs)} неактивных")
        
        for sub in inactive_subs:
            print(f"\n   Канал: {sub['channel_name']}")
            print(f"   ID: {sub['id']}")
            
            choice = input("   Удалить из истории? (y/n/q для выхода): ").strip().lower()
            
            if choice == 'q':
                print("\n⚠️  Прервано пользователем")
                return
            elif choice == 'y':
                db.mark_subscription_deleted(sub['id'])
                print("   ✓ Удалено из истории")
            else:
                print("   ⊘ Пропущено")
    
    print(f"\n{'=' * 80}")
    print("✅ Готово!")
    print('=' * 80)


def delete_all_inactive():
    """Удалить все неактивные подписки"""
    db = Database()
    channels = db.get_all_personal_channels()
    
    total = 0
    
    for channel in channels:
        all_subs = db.get_subscriptions_by_channel(channel['id'], include_inactive=True)
        inactive_subs = [s for s in all_subs if not s['is_active']]
        
        for sub in inactive_subs:
            db.mark_subscription_deleted(sub['id'])
            total += 1
    
    print(f"✅ Удалено из истории: {total} подписок")


def view_statistics():
    """Статистика по подпискам"""
    db = Database()
    channels = db.get_all_personal_channels()
    
    print(f"\n{'=' * 80}")
    print("Статистика подписок")
    print('=' * 80)
    
    total_active = 0
    total_inactive = 0
    total_deleted = 0
    
    for channel in channels:
        all_subs = db.get_subscriptions_by_channel(channel['id'], include_inactive=True)
        
        active = len([s for s in all_subs if s['is_active']])
        inactive = len([s for s in all_subs if not s['is_active']])
        
        # Подсчитываем удалённые (требует отдельного запроса)
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) as count FROM subscriptions 
            WHERE personal_channel_id = ? AND deleted_by_user = 1
        ''', (channel['id'],))
        deleted = cursor.fetchone()['count']
        conn.close()
        
        print(f"\n📺 {channel['name']}:")
        print(f"   Активные: {active}")
        print(f"   Неактивные (в истории): {inactive}")
        print(f"   Удалённые из истории: {deleted}")
        
        total_active += active
        total_inactive += inactive
        total_deleted += deleted
    
    print(f"\n{'=' * 80}")
    print(f"ВСЕГО:")
    print(f"   Активные: {total_active}")
    print(f"   Неактивные: {total_inactive}")
    print(f"   Удалённые: {total_deleted}")
    print('=' * 80)


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == '--delete-inactive':
            delete_all_inactive()
            return
    
    print("=" * 80)
    print("YouTube Dashboard - Управление подписками")
    print("=" * 80)
    
    print("\nВыберите действие:")
    print("1. Просмотр неактивных подписок")
    print("2. Удалить неактивные из истории (интерактивно)")
    print("3. Удалить ВСЕ неактивные из истории")
    print("4. Статистика подписок")
    print("5. Выход")
    
    choice = input("\nВаш выбор (1-5): ").strip()
    
    if choice == '1':
        view_inactive_subscriptions()
    elif choice == '2':
        delete_inactive_interactive()
    elif choice == '3':
        confirm = input("\n⚠️  Удалить ВСЕ неактивные подписки? (yes/no): ").strip().lower()
        if confirm == 'yes':
            delete_all_inactive()
        else:
            print("❌ Отменено")
    elif choice == '4':
        view_statistics()
    elif choice == '5':
        pass
    else:
        print("❌ Некорректный выбор")


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