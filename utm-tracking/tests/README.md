# Tests

Тесты для UTM tracking и ML моделей.

## Структура

```
tests/
├── conftest.py              # Общие fixtures
├── unit/                    # Unit тесты
│   ├── test_markov_chain.py
│   ├── test_early_signals.py
│   ├── test_ltv_predictor.py
│   └── test_creative_analyzer.py
└── integration/             # Integration тесты
    └── test_api_analytics.py
```

## Запуск тестов

### Установка зависимостей

```bash
cd utm-tracking
pip install -r requirements-test.txt
```

### Запуск всех тестов

```bash
pytest
```

### Запуск unit тестов

```bash
pytest tests/unit/
```

### Запуск integration тестов

```bash
pytest tests/integration/
```

### Запуск с coverage

```bash
pytest --cov=utils --cov=api --cov-report=html
```

HTML отчет будет в `htmlcov/index.html`

### Запуск отдельного файла

```bash
pytest tests/unit/test_markov_chain.py
```

### Запуск отдельного теста

```bash
pytest tests/unit/test_markov_chain.py::TestMarkovChainPredictor::test_predict_cvr_exact_match
```

### Запуск с маркерами

```bash
# Только unit тесты
pytest -m unit

# Только integration тесты
pytest -m integration

# Пропустить медленные тесты
pytest -m "not slow"
```

## Fixtures

### Основные fixtures (conftest.py)

- `engine` - SQLite in-memory БД
- `db_session` - Сессия БД для каждого теста
- `test_user` - Тестовый пользователь
- `sample_creatives` - Набор креативов для тестов
- `sample_pattern_performance` - Паттерны производительности
- `sample_traffic_sources` - Трафик источники
- `mock_anthropic_client` - Mock Anthropic API

## Coverage

Цель: 80%+ coverage для основных ML модулей

Текущий coverage:
- `utils/markov_chain.py`: ~90%
- `utils/early_signals.py`: ~95%
- `utils/ltv_predictor.py`: ~90%
- `utils/creative_analyzer.py`: ~70%

## Добавление новых тестов

1. Создайте файл `test_*.py` в соответствующей папке
2. Импортируйте необходимые fixtures из conftest
3. Используйте классы `Test*` для группировки тестов
4. Добавьте маркеры если нужно (@pytest.mark.slow, и т.д.)

Пример:

```python
import pytest

class TestMyFeature:
    def test_basic_case(self, db_session, test_user):
        # Test implementation
        pass

    @pytest.mark.slow
    def test_complex_case(self, sample_creatives):
        # Slow test
        pass
```

## CI/CD

Тесты должны запускаться автоматически при каждом push:

```yaml
# .github/workflows/tests.yml
- name: Run tests
  run: |
    cd utm-tracking
    pytest --cov --cov-report=xml
```

## Troubleshooting

### ImportError

Убедитесь что PYTHONPATH настроен:

```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

### Database errors

Тесты используют in-memory SQLite, не нужна настоящая БД.

### Медленные тесты

Используйте `-m "not slow"` чтобы пропустить медленные тесты.
