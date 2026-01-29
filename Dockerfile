# Dockerfile для запуска автотестов Яндекс.Диска API

FROM python:3.9-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Создаём директорию для отчётов
RUN mkdir -p reports

# Запускаем тесты по умолчанию
CMD ["pytest", "-v"]
