# Verification & Validation — лабораторна №5

**Дата:** 12.11.2026

**Обсяг:** 9 базових REST operations та пошук `ADD-L5-F-001` / Issue #28

**Джерела:** чинні SRS, `spec/openapi.json`, `spec/addendum-lab5.md`

## VERIFICATION — PASS

Перевірено відповідність URI, HTTP methods/status codes, parameters, request/response schemas, `ErrorResponse`, operationId і `x-req-ids`. Усі 9 базових operations та `search` реалізовані й простежуються до затверджених вимог.

| Обсяг | Позитивні сценарії | Негативні та граничні сценарії | Результат |
|---|---|---|---|
| Category: POST, GET, PATCH, DELETE | CRUD, список, persistence | назва 1/50/51, trim, тип, унікальність, ID, 400/404/405/409/415/422, `CATEGORY_IN_USE` | PASS |
| Transaction: POST, GET, PATCH, DELETE | CRUD, список, AND-фільтри, сортування, persistence | сума, дата, тип, Category, description 0/255/256, ID, malformed/media type, 400/404/405/415/422/500, rollback | PASS |
| Financial Summary | порожня БД, доходи, витрати, баланс, перерахунок | від’ємний баланс, десяткова точність, незалежність від Filter | PASS |
| `ADD-L5-F-001` | trim, український Unicode `casefold()`, literal substring, AND і сортування | 1/255/256, порожній/пробільний/повторений `search`, `%`/`_`/code syntax, no match, `description: null` | PASS |
| Generated OpenAPI | responses і Transaction query parameters | `ErrorResponse`, search-specific 422 rules | PASS |

Команди та фактичні результати:

```powershell
python -m pytest -q -p no:cacheprovider
# 160 passed, 0 failed, 0 skipped; 1 TestClient deprecation warning

python -m pytest tests/test_openapi_documentation.py -q -p no:cacheprovider
# 4 passed, 0 failed, 0 skipped

npx --yes @redocly/cli@2.72.1 lint spec/openapi.json
# valid; 0 errors, 2 warnings
```

Redocly warnings не є невідповідностями API: у `info` немає `license`, а затверджений локальний server використовує `localhost`. Невідповідностей реалізації вимогам або контракту не виявлено.

Обмеження автоматичної перевірки: pytest використовує TestClient, а не браузер і окремий live server. У поточному Python environment та `requirements.txt` немає `uvicorn`; перед ручним запуском потрібен ASGI runner. Це не впливає на 160 автоматизованих tests, але є інфраструктурною передумовою ручної валідації.

## VALIDATION — PASS від 12.11.2026

Студентка особисто провела ручну валідацію через Swagger UI `http://127.0.0.1:8000/docs`. Усі перевірені сценарії дали очікувані результати; реалізацію REST API визнано прийнятною.

| Перевірений сценарій | Очікуваний результат | Фактичний результат |
|---|---|---|
| Category CRUD | Створення, список, редагування й видалення повертають контрактні відповіді та змінюють потрібний ресурс | PASS — поведінка відповідає очікуваній |
| Transaction CRUD | Створення, список, часткове редагування й видалення працюють за контрактом | PASS — поведінка відповідає очікуваній |
| Financial Summary після PATCH/DELETE | Показники перераховуються за актуальними Transaction | PASS — значення перераховано правильно |
| Пошук `description` | Trim, пошук без урахування регістру та AND з іншими Filter повертають лише відповідні Transaction | PASS — отримано очікувані записи |
| Помилки й порожній результат пошуку | Некоректний `search` дає 422, відсутність збігів — `200 []` | PASS — отримано очікувані статуси й відповіді |
| Незалежність Financial Summary | Filter/search списку не змінюють загальні фінансові показники | PASS — підсумки залишилися незалежними |

**Рішення студентки:** реалізація відповідає практичним потребам і затвердженим сценаріям; VALIDATION завершено зі статусом PASS від 12.11.2026.

Скриншоти ручної перевірки збережені локально та будуть оформлені пізніше як додаток до звіту.

### Локальний запуск

З кореня проєкту у PowerShell:

```powershell
python -m pip install -r requirements.txt
python -m pip install "uvicorn[standard]"
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000
```

Swagger UI: `http://127.0.0.1:8000/docs`

OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

### Практичні сценарії Swagger UI

1. **Category CRUD.** Створити `income` Category «Зарплата», `expense` Category «Їжа» і тимчасову Category; виконати GET списку, PATCH назви тимчасової Category та DELETE. Очікувати 201/200/200/204 і незмінні ID.
2. **Transaction CRUD.** З отриманими Category ID створити income та expense Transaction. Для POST/PATCH передати `X-Client-Local-Date: 2026-11-12`, а `date` — не пізніше цієї дати. Перевірити GET, частковий PATCH, DELETE і повторний GET; очікувати повні JSON records, 200/204 та відсутність видаленої Transaction.
3. **Пошук Issue #28.** Створити кілька Transaction з описами «Щомісячна премія за жовтень», іншим текстом і `null`. Виконати GET із `search` = `  ПРЕМІЯ  `, потім разом із type/category/date filters. Очікувати literal case-insensitive збіги, AND-перетин і сортування за date DESC. Окремо передати пробіли та 256 символів: очікувати 422 з `non_blank` і `max_length_255`.
4. **Financial Summary.** До й після PATCH/DELETE Transaction викликати GET `/api/financial-summary`; порівняти доходи, витрати та баланс. Попередній GET `/api/transactions` із Filter/search не повинен змінити підсумки.

Наведені сценарії виконані студенткою вручну та завершені з очікуваними результатами.
