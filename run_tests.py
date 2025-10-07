#!/usr/bin/env python3
"""
Скрипт для запуска тестов с различными опциями
"""

import sys
import subprocess
import argparse


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
    
    print(f"Запуск: {' '.join(cmd)}")
    print("=" * 60)
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n" + "=" * 60)
        print("✅ Все тесты пройдены!")
        if coverage:
            print("\nОтчёт coverage: htmlcov/index.html")
    else:
        print("\n" + "=" * 60)
        print("❌ Некоторые тесты не прошли")
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