# File Analyzer Service

Веб-сервис на FastAPI для автоматического скачивания текстовых файлов во внешнем хранилище, сохранения их локально и в базу данных SQLite, а также анализа частоты встречаемости цифр (0–9) в содержимом этих файлов.

## Технологический стек
* Language: Python 3.11+
* Framework: FastAPI (Uvicorn)
* ORM & Database: SQLAlchemy 2.0 (AsyncIO) + SQLite (aiosqlite)
* HTTP Client: httpx (асинхронное взаимодействие с внешней API)
* Validation & Settings: Pydantic v2 / Pydantic Settings
* Frontend: HTML5, CSS3, Jinja2, Alpine.js (реактивный UI)
* Testing: pytest, pytest-asyncio, httpx.MockTransport

## Структура проекта

``` text
file-analyzer-service/
├── src/
│   ├── api/
│   │   ├── downloader.py      # Роутер для управления пайплайном скачивания
│   │   └── routers.py         # Роутеры UI и API (получение файлов, расчет статистики)
│   ├── config.py              # Настройки Pydantic Settings (чтение .env)
│   ├── database.py            # Настройка асинхронного движка и сессий SQLAlchemy
│   ├── models.py              # Декларативные модели БД (DownloadFile, DownloadProgress)
│   ├── schemas.py             # Схемы валидации и сериализации Pydantic v2
│   ├──── services/
│   │     ├── analyzer.py        # Сервис анализа файлов
│   │     └── downloader.py      # Сервис выкачивания файлов
│   ├── templates/             # Jinja2 HTML-шаблоны (base.html, files.html, etc.)
│   └── static/                # Статические файлы (CSS, JS)
├── storage/                   # Локальное хранилище для скачанных текстовых файлов
├── tests/                     # Асинхронные интеграционные и unit-тесты
├── .env.example               # Пример конфигурационного файла
├── main.py                    # Точка входа FastAPI приложения
└── requirements.txt           # Зависимости проекта
```
## Ключевой функционал
1. Автоматическое скачивание файлов (DownloadService):
* Получение списков имен файлов с внешнего сервиса.
* Пакетное (батчевое) скачивание ZIP-архивов с файлами (по 3 файла в батче).
* Распаковка и сохранение текстового содержимого локально в storage/ и в БД.
* Обход антифрода и rate-limiting: обработка HTTP-статусов 429 / 403 с паузой по заголовку Retry-After.
* Подтверждение успешного скачивания на внешнем сервере.
2. UI и Пагинация файлов:
* Отображение загруженных файлов в виде таблицы с постраничной пагинацией (10 файлов на страницу).
* Выбор отдельных файлов или всех файлов в базе данных с помощью чекбоксов.
3. Анализ частоты цифр (FileAnalyzerService):
* Подсчет количества вхождений цифр от 0 до 9 для выбранного списка файлов или для всей базы целиком.
* Возврат агрегированной общей статистики и подробной разбивки по каждому файлу.

## Установка и запуск

### 1. Клонирование репозитория и настройка окружения
```bash
git clone <URL_ВАШЕГО_РЕПОЗИТОРИЯ>
cd file-analyzer-service

# Создание и активация виртуального окружения
python -m venv venv
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```
### 2. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 3. Настройка переменных окружения
Создайте файл .env в корневой директории проекта
```ini
PROJECT_NAME="File Analyzer Service"
DEBUG=True
DATABASE_URI="sqlite+aiosqlite:///./src.db"

EXTERNAL_API_BASE_URL="https://external-service.example.com"
CANDIDATE_ID="your_candidate_id"
MAX_FILES_PER_DOWNLOAD_BATCH=3
ADMIN_TOKEN="your_admin_token"
```

### 4. Запуск приложения
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
После запуска приложения автоматическая документация Swagger и ReDoc доступна по адресам:
* **Swagger UI:** [http://127.0.0.1:8000/docs]
* **ReDoc:** [http://127.0.0.1:8000/redoc]
## Запуск тестов
Тестовое покрытие выполнено с использованием pytest и pytest-asyncio.
```bash
pytest
```

## Основные API эндпоинты
### Управление загрузкой

| Метод | Эндпоинт | Статус | Описание |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/download/start` | `202 Accepted` | Запуск фонового пайплайна скачивания файлов |
| `GET` | `/api/download/status` | `200 OK` | Получение текущего статуса и прогресса скачивания |

### Работа с файлами и аналитика

| Метод | Эндпоинт | Статус | Описание |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/files` | `200 OK` | Получение списка файлов с пагинацией (`page`, `page_size`) |
| `POST` | `/api/files/calculate` | `200 OK` | Подсчет частоты цифр (0–9) по ID или по всей базе |

### Веб-интерфейс (HTML)

| Метод | Эндпоинт | Описание |
| :--- | :--- | :--- |
| `GET` | `/` | Главная страница сервиса |
| `GET` | `/download` | Страница запуска и мониторинга загрузки |
| `GET` | `/files` | Страница просмотра файлов и запуска расчетов |

