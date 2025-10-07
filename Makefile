.PHONY: help install install-dev test test-unit test-integration test-cov clean lint format

help:
	@echo "YouTube Dashboard - Команды разработки"
	@echo ""
	@echo "  make install        - Установить зависимости"
	@echo "  make install-dev    - Установить dev зависимости"
	@echo "  make test           - Запустить все тесты"
	@echo "  make test-unit      - Запустить только unit тесты"
	@echo "  make test-integration - Запустить интеграционные тесты"
	@echo "  make test-cov       - Тесты с coverage отчётом"
	@echo "  make lint           - Проверить код (flake8)"
	@echo "  make format         - Форматировать код (black)"
	@echo "  make clean          - Очистить временные файлы"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

test:
	pytest

test-unit:
	pytest -m unit

test-integration:
	pytest -m integration

test-cov:
	pytest --cov=src --cov-report=html --cov-report=term

lint:
	flake8 src/ utils/ tests/ --max-line-length=100

format:
	black src/ utils/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -f .coverage