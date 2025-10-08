#!/usr/bin/env python3
"""
Скрипт для запуска тестов с различными опциями
"""

import sys
import subprocess
import argparse
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from locales.i18n import t, load_locale_from_config

# Загружаем локаль из настроек
load_locale_from_config()


def run_tests(test_type='all', coverage=False, verbose=False):
    """Запуск тестов с заданными параметрами"""
    
    cmd = ['pytest']
    
    # Тип тестов
    if test_type == 'unit':
        cmd.extend(['-m', 'unit'])
    elif test_type == 'integration':
        cmd.extend(['-m', 'integration'])
    elif test_type == 'api':
        cmd.extend(['-m', 'api'])
    
    # Coverage
    if coverage:
        cmd.extend(['--cov=src', '--cov-report=html', '--cov-report=term'])
    
    # Verbose
    if verbose:
        cmd.append('-vv')
    else:
        cmd.append('-v')
    
    print(t('tests.running_command', command=' '.join(cmd)))
    print("=" * 60)

    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("\n" + "=" * 60)
        print(f"✅ {t('tests.all_passed')}")
        if coverage:
            print(f"\n{t('tests.report_location')}")
    else:
        print("\n" + "=" * 60)
        print(f"❌ {t('tests.some_failed')}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Запуск тестов YouTube Dashboard'
    )
    
    parser.add_argument(
        'type',
        nargs='?',
        default='all',
        choices=['all', 'unit', 'integration', 'api'],
        help='Тип тестов для запуска (по умолчанию: all)'
    )
    
    parser.add_argument(
        '-c', '--coverage',
        action='store_true',
        help='Включить coverage отчёт'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Детальный вывод'
    )
    
    args = parser.parse_args()
    
    run_tests(args.type, args.coverage, args.verbose)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(0)
