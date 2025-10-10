#!/usr/bin/env python3
"""
Utility for changing the interface language
"""

import sys
import os
import json

# Add project root folder to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from locales import get_available_locales, set_locale, t


def load_settings():
    """Load settings"""
    settings_path = os.path.join(project_root, 'config', 'settings.json')
    
    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'locale': 'ru'}


def save_settings(settings):
    """Save settings"""
    settings_path = os.path.join(project_root, 'config', 'settings.json')
    os.makedirs(os.path.dirname(settings_path), exist_ok=True)
    
    with open(settings_path, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


def main():
    print("=" * 80)
    print("SubDeck for YouTube - Смена языка / Change Language")
    print("=" * 80)
    
    # Load current settings
    settings = load_settings()
    current_locale = settings.get('locale', 'ru')
    
    print(f"\nТекущий язык / Current language: {current_locale}")
    
    # Get available languages
    available = get_available_locales()
    
    print("\nДоступные языки / Available languages:")
    for i, locale in enumerate(available, 1):
        locale_names = {
            'ru': 'Русский (Russian)',
            'en': 'English',
            'uk': 'Українська (Ukrainian)'
        }
        name = locale_names.get(locale, locale)
        mark = " [текущий/current]" if locale == current_locale else ""
        print(f"  {i}. {locale} - {name}{mark}")
    
    print(f"\n{len(available) + 1}. Отмена / Cancel")
    
    choice = input(f"\nВыберите язык / Choose language (1-{len(available) + 1}): ").strip()
    
    try:
        choice_num = int(choice)
        
        if choice_num == len(available) + 1:
            print("\nОтменено / Cancelled")
            return
        
        if 1 <= choice_num <= len(available):
            new_locale = available[choice_num - 1]
            settings['locale'] = new_locale
            save_settings(settings)
            
            # Set new language
            set_locale(new_locale)
            
            print(f"\n✅ {t('common.success')}!")
            print(f"Язык изменён на / Language changed to: {new_locale}")
            print("\nПерезапустите приложение для применения изменений.")
            print("Restart the application to apply changes.")
        else:
            print("\n❌ Некорректный выбор / Invalid choice")
    
    except ValueError:
        print("\n❌ Некорректный ввод / Invalid input")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем / Interrupted by user")
        sys.exit(0)