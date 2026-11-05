# Лабораторна робота №3. FastAPI та SQLite

**Варіант 6 — «Облік подій поштової безпеки»**: сервіс обліку підсумків перевірки
повідомлень.

| Параметр | Значення |
|---|---|
| Категорії (id 1–3) | `phishing`, `malicious_attachment`, `spam` |
| Назва запису | `Спостереження пошти NN` |
| `value` | ціле число `>= 0` — кількість виявлених подій |
| Одиниця (`unit`) | `events` |
| Поріг | `10` |
| Статуси | `new`, `in_progress`, `done` |

Дробове `value` (наприклад `1.5`), рядок чи `true` дають `422`.

## Структура

```text
labs/lab03/
├── config.py        # одиниця, поріг, обмеження варіанта
├── schema.sql       # готова схема (categories, records)
├── database.py      # з’єднання та створення таблиць
├── schemas.py       # Pydantic-моделі
├── repository.py    # параметризовані SQL-запити, транзакції
├── seed.py          # початкове заповнення з data/seed.json
├── main.py          # FastAPI-застосунок
├── routers/         # categories.py, records.py
└── data/seed.json   # навчальні дані (lab3.sqlite3 не додається до Git)
```

## Встановлення і запуск (з кореня репозиторію)

```bash
pip install -r requirements.txt
python -m labs.lab03.database      # створити таблиці
python -m labs.lab03.seed          # 3 категорії + 8 записів (повторний запуск безпечний)
uvicorn labs.lab03.main:app --reload --host 127.0.0.1 --port 8000
```

Swagger UI: <http://127.0.0.1:8000/docs>, OpenAPI: <http://127.0.0.1:8000/openapi.json>.

## Маршрути

| Метод і шлях | Результат |
|---|---|
| `GET /ping`, `GET /student` | 200 |
| `GET /categories`, `POST /categories`, `DELETE /categories/{id}` | 200 / 201 / 204 (404, 409) |
| `GET /records` (`category_id`, `status`, `min_value`, `q`, `limit`, `offset`) | 200 |
| `GET /records/{id}`, `POST /records`, `PUT /records/{id}`, `DELETE /records/{id}` | 200 / 201 / 200 / 204 (404, 409) |
| `POST /records/bulk` | 201, атомарно; 404 / 409 — нічого не збережено |

## Приклади

```bash
curl -i "http://127.0.0.1:8000/ping"
curl -i "http://127.0.0.1:8000/records?category_id=1&status=new&limit=5&offset=0"

curl -i -X POST "http://127.0.0.1:8000/records" \
  -H "Content-Type: application/json" \
  -d '{"code":"V06-TEST","title":"Навчальна знахідка","category_id":1,"value":7,"status":"new"}'

# відкат пакета: V06-01 уже існує, V06-ROLLBACK не має зберегтися
curl -i -X POST "http://127.0.0.1:8000/records/bulk" \
  -H "Content-Type: application/json" \
  -d '[{"code":"V06-ROLLBACK","title":"Перший елемент","category_id":1,"value":4,"status":"new"},{"code":"V06-01","title":"Дублікат коду","category_id":2,"value":5,"status":"new"}]'

curl -i "http://127.0.0.1:8000/records?q=%27%20OR%201%3D1%20--"   # SQL-ін’єкції немає
```

## Перевірки

```bash
ruff check . && ruff format --check .
pytest
```
