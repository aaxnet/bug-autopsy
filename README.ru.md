<div align="center">

```
██████╗ ██╗   ██╗ ██████╗      █████╗ ██╗   ██╗████████╗ ██████╗ ██████╗ ███████╗██╗   ██╗
██╔══██╗██║   ██║██╔════╝     ██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗██╔══██╗██╔════╝╚██╗ ██╔╝
██████╔╝██║   ██║██║  ███╗    ███████║██║   ██║   ██║   ██║   ██║██████╔╝███████╗ ╚████╔╝
██╔══██╗██║   ██║██║   ██║    ██╔══██║██║   ██║   ██║   ██║   ██║██╔═══╝ ╚════██║  ╚██╔╝
██████╔╝╚██████╔╝╚██████╔╝    ██║  ██║╚██████╔╝   ██║   ╚██████╔╝██║     ███████║   ██║
╚═════╝  ╚═════╝  ╚═════╝     ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝ ╚═╝     ╚══════╝   ╚═╝
```

### Превращает сырые Python-трейсбеки в конкретные решения — за секунды.

<br/>

[![PyPI](https://img.shields.io/pypi/v/bug-autopsy?style=flat-square&color=black)](https://pypi.org/project/bug-autopsy/)
[![Python](https://img.shields.io/badge/python-3.9+-black?style=flat-square)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-black?style=flat-square)](LICENSE)
[![Tests](https://img.shields.io/badge/тесты-39%20прошли-black?style=flat-square)](#)
[![Zero deps](https://img.shields.io/badge/зависимости-ноль-black?style=flat-square)](#)

[![EN](https://img.shields.io/badge/lang-EN-black?style=flat-square)](README.md)
[![Баг](https://img.shields.io/badge/сообщить-об_ошибке-black?style=flat-square&logo=github&logoColor=white)](https://github.com/yourname/bug-autopsy/issues/new)
[![Фича](https://img.shields.io/badge/предложить-функцию-black?style=flat-square&logo=github&logoColor=white)](https://github.com/yourname/bug-autopsy/issues/new)

</div>

---

## Проблема

CI-пайплайн упал. В логах — стена красного текста.

Вы скроллите. Щуритесь. Гуглите ошибку. Находите ответ на Stack Overflow из 2016 года. Может, подойдёт. Может, нет.

**Bug Autopsy решает это.**

Одна команда читает любой лог, трейсбек или дамп ошибки и возвращает структурированный диагноз — корневая причина, оценка уверенности, точное место в стеке и 2–4 конкретных решения — за то время, пока вы дочитываете первую строку.

---

## Установка

```bash
pip install bug-autopsy
```

> Без API-ключей. Без сетевых запросов. Без обязательных зависимостей. Работает на Python 3.9+, Windows / Linux / macOS.

---

## Быстрый старт

### Анализ файла с логами

```bash
autopsy --file path/to/error.log
```

### Анализ текста напрямую

```bash
autopsy --text "ModuleNotFoundError: No module named 'requests'"
```

### Пайп из вашей программы

```bash
python my_script.py 2>&1 | autopsy
```

### Сохранить Markdown-отчёт

```bash
autopsy --file crash.log --report autopsy_report.md
```

---

## Вывод

```
╔══════════════════════════════════════════╗
║         🔬  B U G   A U T O P S Y       ║
╚══════════════════════════════════════════╝
  Обнаружено ошибок: 2

┌─ [1] KeyError
│  Сообщение : KeyError: 'url'
│  Окружение : Database / ORM
│  Уверенность: [███████████████████░] 95%
│
│  🧠 Объяснение
│     Ключ 'url' не найден в словаре. Структура данных
│     не содержит этого ключа в момент обращения.
│
│  📍 Расположение в стеке
│     • startup()  →  /srv/api/main.py:47
│       db_url = config['database']['url']
│     • fallback_connect()  →  /srv/api/db.py:18
│
│  🔧 Рекомендуемые исправления
│   1. Используйте `.get()` с дефолтом: `value = d.get('url', default_value)`
│   2. Проверьте опечатки — ключи чувствительны к регистру.
│   3. Убедитесь, что ключ заполнен перед обращением.
│   4. Добавьте проверку: `if 'url' in d:` перед доступом.
└────────────────────────────────────────────────────────────
```

`autopsy --file crash.log --report report.md` сохраняет полный структурированный Markdown-отчёт:

```markdown
# 🔬 Bug Autopsy Report

**Сгенерирован:** 2025-01-15 14:32:01
**Источник:** `crash.log`
**Найдено ошибок:** 2

| # | Тип ошибки | Уверенность       | Окружение      |
|---|-----------|-------------------|----------------|
| 1 | KeyError  | [██████████] 95%  | Database / ORM |
| 2 | TypeError | [█████████░] 92%  | Database / ORM |

## Ошибка 1: `KeyError`
...
```

---

## Команды

| Команда | Описание |
|---|---|
| `autopsy --file <path>` | Анализ файла с логами или трейсбеком |
| `autopsy --text "<content>"` | Анализ текста ошибки напрямую |
| `cat log.txt \| autopsy` | Пайп из любой команды |
| `autopsy --file <path> --report out.md` | Сохранить Markdown-отчёт |
| `autopsy --file <path> --quiet` | Без вывода в консоль (только отчёт) |
| `autopsy --no-color` | Без ANSI-цветов (для CI) |

---

## Обнаруживаемые типы ошибок

| Тип ошибки | Что ловит |
|---|---|
| `ModuleNotFoundError` | Отсутствующий пакет или неверное виртуальное окружение |
| `ImportError` | Неверное имя импорта, циклический импорт, сломанная установка |
| `KeyError` | Ключ отсутствует в словаре |
| `IndexError` | Индекс списка выходит за пределы |
| `TypeError` | Неверный тип в функции или операции |
| `NameError` | Переменная используется до присвоения |
| `AssertionError` | Провальный assert или нарушение инварианта |
| `PermissionError` | Отказ в доступе к файловой системе ОС |
| `TimeoutError` | Превышено время ожидания сети или I/O |
| `AttributeError` | Атрибут не найден на объекте |
| `ZeroDivisionError` | Деление на ноль |
| `FileNotFoundError` | Файл или директория не существует |
| `RecursionError` | Превышена максимальная глубина рекурсии |
| `UnicodeDecodeError` | Несовпадение кодировки при чтении байтов |
| `ValueError` | Верный тип, неверное значение |
| `MemoryError` | Нехватка оперативной памяти |
| `RuntimeError` | Общая ошибка времени выполнения |
| `OSError` | Низкоуровневая ошибка ОС |
| `StopIteration` | Исчерпанный итератор вне генератора |

---

## Определение окружения

Bug Autopsy автоматически определяет среду, из которой пришла ошибка, и адаптирует контекст.

| Окружение | Ключевые слова |
|---|---|
| Flask (веб-бэкенд) | `flask`, `werkzeug`, `Blueprint` |
| FastAPI (веб-бэкенд) | `fastapi`, `uvicorn`, `APIRouter` |
| Django (веб-бэкенд) | `django`, `wsgi`, `migrations` |
| Фреймворк тестирования | `pytest`, `unittest`, `TestCase` |
| База данных / ORM | `sqlalchemy`, `psycopg2`, `sqlite3` |
| Data science / ML | `pandas`, `numpy`, `torch`, `sklearn` |
| Очередь задач | `celery`, `dramatiq`, `rq` |
| AWS / облако | `boto3`, `lambda_handler` |

---

## Python API

Bug Autopsy можно использовать программно в ваших скриптах и инструментах:

```python
from autopsy.analyzer import analyze
from autopsy import report as report_mod

log_text = open("crash.log").read()
results = analyze(log_text)

for r in results:
    print(f"{r.error_type} — уверенность {r.confidence:.0%}")
    print(r.explanation)
    for fix in r.fixes:
        print(f"  • {fix}")

# Сохранить Markdown-отчёт
md = report_mod.generate(results, source_label="crash.log")
report_mod.save(md, "autopsy_report.md")
```

Каждый объект `DiagnosticResult` содержит:

```python
r.error_type    # "KeyError"
r.message       # исходная совпавшая строка
r.confidence    # 0.0 – 1.0
r.explanation   # объяснение корневой причины
r.fixes         # список рекомендаций
r.context       # определённое окружение ("Flask", "pytest", ...)
r.frames        # распарсенные фреймы стека (файл, строка, функция, код)
r.raw_excerpt   # окружающий контекст из лога
```

---

## Структура проекта

```
bug-autopsy/
├── autopsy/
│   ├── analyzer.py     # Ядро: парсинг, детекция и классификация
│   ├── cli.py          # Интерфейс командной строки
│   └── report.py       # Генерация Markdown-отчётов
├── examples/
│   ├── module_not_found.log
│   ├── multi_error.log
│   ├── flask_error.log
│   └── sample_report.md
├── tests/
│   ├── test_analyzer.py
│   └── test_report.py
├── pyproject.toml
└── README.md
```

---

## Запуск тестов

```bash
# Установка с dev-зависимостями
pip install -e ".[dev]"

# Все тесты
pytest

# С покрытием
pytest --cov=autopsy --cov-report=term-missing
```

Все **39 тестов** проходят на Python 3.9 – 3.12.

---

## Дорожная карта

- AI-объяснения через LLM
- Анализатор GitHub Issues
- Песочница для автовоспроизведения ошибок
- Система предложения авто-патчей
- Веб-интерфейс (FastAPI)

---

## Участие в разработке

```bash
git clone https://github.com/yourname/bug-autopsy
cd bug-autopsy
pip install -e ".[dev]"
pytest
```

PR приветствуются. Смотрите [открытые задачи](https://github.com/yourname/bug-autopsy/issues).

---

<div align="center">
<br/>

Если Bug Autopsy сэкономил вам сессию отладки — ⭐ поможет другим разработчикам его найти.

<br/>

[![Star on GitHub](https://img.shields.io/badge/Звезда_на_GitHub-black?style=flat-square&logo=github&logoColor=white)](https://github.com/yourname/bug-autopsy)
[![PyPI](https://img.shields.io/badge/PyPI-black?style=flat-square&logo=pypi&logoColor=white)](https://pypi.org/project/bug-autopsy/)
[![Сообщить об ошибке](https://img.shields.io/badge/Сообщить_об_ошибке-black?style=flat-square&logo=github&logoColor=white)](https://github.com/yourname/bug-autopsy/issues/new)

<br/>
</div>
