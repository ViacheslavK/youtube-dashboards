# GitHub Actions Workflows

## Автоматизация CI/CD для YouTube Dashboard

### 📋 Workflows

#### 1. **test.yml** - Continuous Integration

**Триггеры:**
- Push в ветки: `main`, `develop`, `feature/**`
- Pull Request в `main`, `develop`

**Что делает:**
- ✅ Запускает тесты на Python 3.9, 3.10, 3.11, 3.12
- ✅ Тестирует на Ubuntu и Windows
- ✅ Генерирует coverage отчёт
- ✅ Загружает отчёт в Codecov (опционально)
- ✅ Проверяет код линтером (flake8)
- ✅ Проверяет форматирование (black)
- ✅ Тестирует миграции БД

**Статус:**
```
[![Tests](https://github.com/YOUR_USERNAME/youtube-dashboard/actions/workflows/test.yml/badge.svg)](https://github.com/YOUR_USERNAME/youtube-dashboard/actions/workflows/test.yml)
```

---

#### 2. **release.yml** - Release Automation

**Триггеры:**
- Push в ветку `main` с тегом `v*.*.*`

**Что делает:**
- ✅ Запускает тесты перед релизом
- ✅ Создаёт GitHub Release
- ✅ Генерирует changelog автоматически
- ✅ Собирает артефакты для Windows и Linux
- ✅ Загружает артефакты в Release

**Создание релиза:**
```bash
# Создать тег
git tag -a v1.0.0 -m "Release v1.0.0"

# Отправить тег
git push origin v1.0.0
```

---

#### 3. **codeql.yml** - Security Scanning

**Триггеры:**
- Push в `main`, `develop`
- Pull Request в `main`
- Еженедельно (понедельник, 00:00)

**Что делает:**
- 🔒 Сканирует код на уязвимости
- 🔒 Проверяет зависимости
- 🔒 Создаёт алерты в GitHub Security

---

### 🎯 Использование

#### Для разработчиков:

**При работе с feature веткой:**
```bash
git checkout -b feature/my-feature
# Делаете изменения
git add .
git commit -m "feat: add new feature"
git push origin feature/my-feature
```

→ Автоматически запустятся тесты

**При создании Pull Request:**
```bash
# Создайте PR в GitHub
# main <- feature/my-feature
```

→ Тесты запустятся для PR

**При мердже в main:**
```bash
# После одобрения PR и мерджа
```

→ Только тесты (без релиза, если нет тега)

---

#### Для мейнтейнеров:

**Создание релиза:**

1. Обновите версию в нужных файлах
2. Создайте тег:
   ```bash
   git tag -a v1.0.0 -m "Release v1.0.0"
   git push origin v1.0.0
   ```
3. GitHub Actions автоматически:
   - Запустит тесты
   - Создаст Release
   - Соберёт артефакты
   - Опубликует всё на GitHub

---

### 📊 Coverage Badge

Добавьте в README.md:

```markdown
[![codecov](https://codecov.io/gh/YOUR_USERNAME/youtube-dashboard/branch/main/graph/badge.svg)](https://codecov.io/gh/YOUR_USERNAME/youtube-dashboard)
```

Настройте Codecov:
1. Зайдите на https://codecov.io/
2. Подключите репозиторий
3. Coverage будет загружаться автоматически

---

### 🔧 Настройка

#### Secrets (если нужны):

Перейдите в: `Settings` → `Secrets and variables` → `Actions`

Добавьте (если необходимо):
- `CODECOV_TOKEN` - для Codecov
- Другие секреты

#### Branch Protection Rules:

Рекомендуется для `main`:
1. `Settings` → `Branches` → `Add rule`
2. Branch name pattern: `main`
3. Включите:
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date
   - ✅ Status checks: `Test on Python 3.12 (ubuntu-latest)`
   - ✅ Require pull request reviews

---

### 📈 Мониторинг

**Просмотр запусков:**
```
Repository → Actions → Select workflow
```

**Просмотр логов:**
```
Actions → Select run → Select job → View logs
```

**Скачать артефакты:**
```
Actions → Select release run → Artifacts section
```

---

### 🐛 Troubleshooting

**Тесты падают в CI, но локально работают:**
- Проверьте версию Python
- Проверьте зависимости (`pip list`)
- Проверьте переменные окружения

**Release не создаётся:**
- Проверьте формат тега (`v*.*.*`)
- Проверьте, что тесты прошли
- Проверьте permissions в workflow

**Dependabot не работает:**
- Проверьте `.github/dependabot.yml`
- Проверьте, что dependabot включён в настройках

---

### 📚 Дополнительно

**Полезные ссылки:**
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Codecov Documentation](https://docs.codecov.com/)
- [Dependabot Configuration](https://docs.github.com/en/code-security/dependabot)

**Best Practices:**
- Всегда тестируйте перед мерджем в main
- Используйте семантическое версионирование (SemVer)
- Пишите осмысленные commit messages
- Создавайте changelog для релизов