#!/bin/bash

# Web Application - Запуск одной командой
# Требования: Docker и Docker Compose

set -e

echo "🚀 Запуск веб-приложения..."
echo ""

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не найден. Пожалуйста, установите Docker."
    exit 1
fi

# Проверка наличия Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose не найден. Пожалуйста, установите Docker Compose."
    exit 1
fi

# Определение команды docker-compose
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    COMPOSE_CMD="docker compose"
fi

# Переход в директорию проекта
cd "$(dirname "$0")"

# Сборка и запуск контейнеров
echo "📦 Сборка образов..."
$COMPOSE_CMD build

echo "🔧 Запуск сервисов (PostgreSQL, Backend, Frontend)..."
$COMPOSE_CMD up -d

echo ""
echo "✅ Приложение запущено!"
echo ""
echo "📍 Frontend: http://localhost"
echo "📍 Backend API: http://localhost:8000"
echo "📍 Swagger Docs: http://localhost:8000/docs"
echo ""
echo "📊 Для просмотра логов выполните:"
echo "   $COMPOSE_CMD logs -f"
echo ""
echo "⏹️  Для остановки выполните:"
echo "   $COMPOSE_CMD down"
echo ""
