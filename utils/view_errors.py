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
        print("✅ Нет нерешённых ошибок синхронизации!")
        return
    
    print(f"\n{'=' * 80}")
    print(f"⚠️  Найдено {len(errors)} нерешённых ошибок")
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
        print(f"Тип: {error_type} ({len(errs)} ошибок)")
        print('─' * 80)
        
        for err in errs[:10]:  # Показываем первые 10
            occurred = datetime.fromisoformat(err['occurred_at'])
            print(f"\nID: {err['id']}")
            print(f"Канал: {err['channel_name']}")
            print(f"Когда: {occurred.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Показываем короткое сообщение
            msg = err['error_message']
            if len(msg) > 100:
                msg = msg[:100] + "..."
            print(f"Сообщение: {msg}")
        
        if len(errs) > 10:
            print(f"\n... и ещё {len(errs) - 10} ошибок этого типа")
    
    print(f"\n{'=' * 80}")


def view_errors_by_channel():
    """Показать ошибки по каналам"""
    db = Database()
    
    channels = db.get_all_personal_channels()
    
    print(f"\n{'=' * 80}")
    print("Ошибки по каналам")
    print('=' * 80)
    
    total_errors = 0
    
    for channel in channels:
        errors = db.get_unresolved_errors(channel['id'])
        
        if errors:
            print(f"\n📺 {channel['name']}: {len(errors)} ошибок")
            
            # Группируем по типу
            error_types = {}
            for err in errors:
                error_types[err['error_type']] = error_types.get(err['error_type'], 0) + 1
            
            for error_type, count in error_types.items():
                print(f"   - {error_type}: {count}")
            
            total_errors += len(errors)
    
    if total_errors == 0:
        print("\n✅ Нет нерешённых ошибок!")
    else:
        print(f"\n{'=' * 80}")
        print(f"Всего нерешённых ошибок: {total_errors}")
        print('=' * 80)


def explain_errors():
    """Объяснение типов ошибок"""
    print(f"\n{'=' * 80}")
    print("Типы ошибок и их значение")
    print('=' * 80)
    
    explanations = {
        'PLAYLIST_NOT_FOUND': 
            'Канал не имеет публичного плейлиста с загруженными видео.\n'
            'Возможные причины:\n'
            '  - Topic-канал (автоматический канал YouTube Music)\n'
            '  - Канал удалён или заблокирован\n'
            '  - У канала нет публичных видео\n'
            'Решение: Можно отписаться от таких каналов',
        
        'DURATION_PARSE_ERROR':
            'Ошибка при обработке длительности видео.\n'
            'Возможные причины:\n'
            '  - Livestream (прямая трансляция)\n'
            '  - Премьера (ещё не началась)\n'
            '  - Некорректные данные от YouTube API\n'
            'Решение: Обычно исправляется автоматически при следующей синхронизации',
        
        'QUOTA_EXCEEDED':
            'Превышена дневная квота YouTube API (10,000 units).\n'
            'Решение: Подождите до следующего дня (квоты обновляются в полночь PST)',
        
        'UNKNOWN':
            'Неизвестная ошибка.\n'
            'Решение: Проверьте детали ошибки или сообщите разработчику'
    }
    
    for error_type, explanation in explanations.items():
        print(f"\n{error_type}:")
        print(f"{explanation}")
    
    print(f"\n{'=' * 80}")


def main():
    print("=" * 80)
    print("YouTube Dashboard - Просмотр ошибок синхронизации")
    print("=" * 80)
    
    print("\nВыберите действие:")
    print("1. Показать все нерешённые ошибки")
    print("2. Показать ошибки по каналам")
    print("3. Объяснение типов ошибок")
    print("4. Выход")
    
    choice = input("\nВаш выбор (1-4): ").strip()
    
    if choice == '1':
        view_errors()
    elif choice == '2':
        view_errors_by_channel()
    elif choice == '3':
        explain_errors()
    elif choice == '4':
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