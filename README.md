# Яндекс.Диск API — Автотесты

Проект автотестов для тестирования REST API Яндекс.Диска.

## Описание

Проект содержит набор автоматизированных тестов для проверки работы API Яндекс.Диска.  
Тесты покрывают основные HTTP-методы: **GET**, **POST**, **PUT**, **DELETE**, а также интеграционные сценарии.

## Установка и запуск

1 способ:

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd test
```

### 2. Создание виртуального окружения

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# или
venv\Scripts\activate     # Windows
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка токена

Скопируйте файл `.env.example` в `.env` (если нужно):

```bash
cp .env.example .env
```

Откройте `.env` и вставьте ваш OAuth‑токен или оставьте токен тестового пользователя

2 способ: Запуск через Docker

**Требования:** Docker и Docker Compose должны быть установлены.

**запуск:**

```bash
# Запуск всех тестов
docker-compose run --rm tests

# Запуск конкретного теста
docker-compose run --rm tests pytest tests/test_yandex_disk_api.py::TestGetMethods::test_get_disk_info

# Запуск по маркерам
docker-compose run --rm tests pytest -m get
docker-compose run --rm tests pytest -m smoke
```

**Сборка образа:**

```bash
docker-compose build
```

**Просмотр отчётов:**
После запуска тестов отчёт будет доступен в `reports/report.html` на хосте.

#### Вариант 3: Запуск через Dockerfile напрямую

```bash
# Сборка образа
docker build -t yandex-disk-tests .

# Запуск тестов
docker run --rm -v $(pwd)/reports:/app/reports yandex-disk-tests

# С передачей токена через переменную окружения
docker run --rm \
  -v $(pwd)/reports:/app/reports \
  -e YANDEX_DISK_TOKEN=your_token_here \
  yandex-disk-tests
```

### 6. Локальный запуск (без Docker)

#### Запуск всех тестов

```bash
pytest
```

#### Запуск отдельных тестов

**По маркерам (группы тестов):**

```bash
pytest -m smoke      # только смоук‑тесты (быстрые проверки)
pytest -m get        # только GET‑тесты
pytest -m post       # только POST‑тесты
pytest -m put        # только PUT‑тесты
pytest -m delete     # только DELETE‑тесты
```

**Конкретный тест:**

```bash
pytest tests/test_yandex_disk_api.py::TestGetMethods::test_get_disk_info
```

**Конкретный класс тестов:**

```bash
pytest tests/test_yandex_disk_api.py::TestGetMethods
```
