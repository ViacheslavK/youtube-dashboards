.PHONY: help install install-dev test test-unit test-integration test-cov clean lint format

help:
	@echo "SubDeck for YouTube - Development commands"
	@echo ""
	@echo "  make install        - Install dependencies"
	@echo "  make install-dev    - Install dev dependencies"
	@echo "  make test           - Run all tests"
	@echo "  make test-unit      - Run only unit tests"
	@echo "  make test-integration - Run integration tests"
	@echo "  make test-cov       - Tests with coverage report"
	@echo "  make lint           - Check code (flake8)"
	@echo "  make format         - Format code (black)"
	@echo "  make clean          - Clean temporary files"

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