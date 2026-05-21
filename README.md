# Web Application - Инструкция по запуску

## Описание проекта

Веб-приложение с функционалом:
- **Авторизация/Регистрация** - JWT токены с автоматическим обновлением
- **Файлы** - Загрузка изображений (до 15 файлов) и видео (до 600MB), просмотр и скачивание
- **Пользователи** - Управление профилем и пользователями (логин, пароль, ФИО, компания, должность)
- **Журналирование** - Логирование всех действий сервера и клиентов

## Технологии

- Backend: Python + FastAPI
- Frontend: HTML/CSS/JavaScript (ванильный)
- БД: PostgreSQL
- Контейнеризация: Docker + Docker Compose

---

## Вариант 1: Запуск одной командой (Рекомендуется)

### Требования
- Docker версии 20.10+
- Docker Compose версии 2.0+

### Запуск

```bash
cd /workspace
./start.sh
```

Или сразу из любой директории:

```bash
/workspace/start.sh
```

### Остановка

```bash
docker-compose down
# или
docker compose down
```

### Доступ к приложению

- Frontend: http://localhost
- Backend API: http://localhost:8000
- API документация (Swagger): http://localhost:8000/docs

### Просмотр логов

```bash
docker-compose logs -f
# или
docker compose logs -f
```

---

## Вариант 2: Запуск через Docker Compose вручную

```bash
cd /workspace
docker-compose up -d --build
# или
docker compose up -d --build
```

---

## Вариант 3: Запуск без Docker (Локальная разработка)

### Требования

- Python 3.9+
- PostgreSQL 13+
- Node.js (опционально, для фронтенда)

### Установка зависимостей

```bash
cd /workspace/backend
pip install -r requirements.txt
```

### Настройка PostgreSQL

```sql
CREATE DATABASE webapp;
CREATE USER postgres WITH PASSWORD 'postgres';
GRANT ALL PRIVILEGES ON DATABASE webapp TO postgres;
```

### Запуск backend

```bash
cd /workspace/backend
export POSTGRES_HOST=localhost
python main.py
```

Или через uvicorn:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Запуск frontend

Просто откройте файл `frontend/index.html` в браузере или используйте любой статический сервер:

```bash
cd /workspace/frontend
python -m http.server 80
```

---

## Вариант 4: Создание исполняемого файла (.exe / elf)

### Для Linux (создание .elf)

```bash
cd /workspace
pip install pyinstaller
pyinstaller --onefile --name=webapp_server scripts/run_server.py
```

Исполняемый файл появится в папке `dist/webapp_server`

### Для Windows (создание .exe)

На Windows машине:

```bash
cd /workspace
pip install pyinstaller
pyinstaller --onefile --name=webapp_server.exe scripts/run_server.py
```

### Запуск исполняемого файла

```bash
# Убедитесь, что PostgreSQL запущен
./dist/webapp_server
```

---

## Переменные окружения

| Переменная | Описание | Значение по умолчанию |
|------------|----------|----------------------|
| POSTGRES_USER | Пользователь БД | postgres |
| POSTGRES_PASSWORD | Пароль БД | postgres |
| POSTGRES_DB | Имя БД | webapp |
| POSTGRES_HOST | Хост БД | db (localhost для локального запуска) |
| POSTGRES_PORT | Порт БД | 5432 |
| SECRET_KEY | Секретный ключ JWT | ваш-секретный-ключ |
| ACCESS_TOKEN_EXPIRE_MINUTES | Время жизни access токена | 30 |
| REFRESH_TOKEN_EXPIRE_DAYS | Время жизни refresh токена | 7 |
| MAX_FILE_SIZE | Максимальный размер файла (байты) | 629145600 (600MB) |
| UPLOAD_DIR | Директория для загрузки файлов | /app/uploads |

---

## API Endpoints

### Авторизация
- `POST /api/auth/register` - Регистрация нового пользователя
- `POST /api/auth/login` - Вход (возвращает JWT токены)
- `POST /api/auth/refresh` - Обновление токенов
- `GET /api/auth/me` - Получение информации о текущем пользователе

### Файлы
- `POST /api/files/upload` - Загрузка файлов (multipart/form-data)
- `GET /api/files/` - Список файлов пользователя
- `GET /api/files/{id}` - Скачивание файла
- `GET /api/files/{id}/view` - Просмотр файла в браузере
- `DELETE /api/files/{id}` - Удаление файла

### Пользователи
- `GET /api/users/me` - Мой профиль
- `PUT /api/users/me` - Обновление профиля
- `GET /api/users/` - Список всех пользователей
- `POST /api/users/` - Создание пользователя
- `PUT /api/users/{id}` - Обновление пользователя
- `DELETE /api/users/{id}` - Удаление пользователя
- `GET /api/users/logs` - Журнал действий

---

## Структура проекта

```
/workspace
├── backend/
│   ├── main.py           # Точка входа FastAPI
│   ├── config.py         # Конфигурация
│   ├── database.py       # Модели БД
│   ├── auth.py           # JWT и хеширование паролей
│   ├── auth_routes.py    # Маршруты авторизации
│   ├── file_routes.py    # Маршруты работы с файлами
│   ├── user_routes.py    # Маршруты управления пользователями
│   ├── logging_service.py # Сервис журналирования
│   ├── requirements.txt  # Python зависимости
│   └── Dockerfile
├── frontend/
│   ├── index.html        # SPA приложение
│   ├── nginx.conf        # Конфигурация nginx
│   └── Dockerfile
├── scripts/
│   └── run_server.py     # Скрипт для создания exe/elf
├── docker-compose.yml    # Docker Compose конфигурация
└── README.md            # Этот файл
```

---

## Безопасность

1. Измените `SECRET_KEY` в production среде
2. Используйте HTTPS в production
3. Ограничьте CORS для конкретных доменов
4. Регулярно обновляйте зависимости

---

## Поддержка

При возникновении проблем:
1. Проверьте логи контейнеров: `docker-compose logs`
2. Убедитесь, что PostgreSQL доступен
3. Проверьте переменные окружения
