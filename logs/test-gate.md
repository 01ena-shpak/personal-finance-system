# TEST-GATE: Category API

**Дата перевірки:** 2026-11-11  
**Обсяг:** тести `POST`, `GET`, `PATCH`, `DELETE /api/categories` до реалізації API та SQLite  
**Рішення:** **GO** — затверджено студенткою 2026-11-11 для початку поетапної реалізації

## Результат перевірки

Тести звірено із SRS, `AC-010`–`AC-015`, `BDD-001`–`BDD-004`, API-сценаріями та `spec/openapi.json`. Перевірки не фіксують порядок елементів GET, не вимагають конкретного значення нового ID і не задають відсутні в контракті назви `rule`. Для неоднозначного PATCH body `{"type":"income"}` допускається `field` `name` або `type`, оскільки контракт не визначає пріоритет між відсутнім і забороненим полем.

Команда:

```powershell
python -m pytest tests/test_categories_api.py -q --tb=line -p no:cacheprovider
```

Результат: **41 collected; 25 RED; 16 SKIPPED; 1 warning**.

- 19 POST cases очікувано отримали `404` замість контрактних `201`, `400`, `409`, `415` або `422`.
- 6 незалежних PATCH/DELETE cases для некоректного path ID очікувано отримали `404` замість `422`.
- Усі RED спричинені відсутністю Category routes; помилок collection, fixtures або синтаксису немає.
- Warning стосується deprecation у FastAPI/Starlette TestClient і не визначає результат тестів.

## Заблоковані сценарії

16 cases тимчасово залишено SKIPPED: GET порожнього й заповненого списку; успішний PATCH; PATCH відсутньої Category, невалідного body та конфлікту назв; успішний DELETE, DELETE відсутньої або використаної Category та повторний DELETE. Вони потребують ізольованої SQLite, робочого POST Category, а для `CATEGORY_IN_USE` — також Transaction. До появи цих передумов їх результат не є доказом RED відповідної operation.

## Умова наступного кроку

Студентка підтвердила 25 RED і затвердила TEST-GATE `GO`. Активні cases готові керувати мінімальною реалізацією routes і contract validation. Кожен із 16 тимчасово SKIPPED cases потрібно активувати та повторно перевірити до реалізації відповідної поведінки; перед зняттям SKIP потрібна function-scoped тестова SQLite з гарантованим порожнім станом, а stateful передумови мають створюватися всередині тесту.

## Поетапна активація після TEST-GATE GO

- **GET `/api/categories` — RED:** 2026-11-11 активовано 2 cases; обидва отримали `405` замість `200`. Порожня ізольована SQLite та POST-передумови працюють, тому RED підтверджує відсутність GET operation. Реалізацію дозволяє затверджений TEST-GATE `GO`.
- **GET `/api/categories` — GREEN:** 2 cases PASS після мінімальної реалізації списку.
- **PATCH `/api/categories/{category_id}` — RED:** активовано 10 stateful cases разом із 3 path-validation cases; 13/13 FAIL через відсутність PATCH operation (`404` замість `200`, `409` або `422`, а для відсутнього ресурсу — неконтрактний 404 body). POST-передумови й ізоляція БД PASS. Реалізацію дозволяє затверджений TEST-GATE `GO`.
- **PATCH `/api/categories/{category_id}` — GREEN:** 13 cases PASS після реалізації перейменування, validation, 404 і 409.
- **DELETE `/api/categories/{category_id}` — RED:** активовано 3 stateful cases разом із 3 path-validation cases; 6/6 FAIL через відсутність DELETE operation (`405` замість `204`, `404` або `422`). `CATEGORY_IN_USE` залишено SKIPPED до реалізації Transaction. Реалізацію решти DELETE дозволяє затверджений TEST-GATE `GO`.
- **DELETE `/api/categories/{category_id}` — GREEN:** 6 cases PASS; `CATEGORY_IN_USE` залишається єдиним SKIPPED.
- **Підсумковий Category regression:** 40 PASS, 0 FAIL, 1 SKIPPED; рішення TEST-GATE `GO` залишається чинним.

---

# TEST-GATE: Transaction API

**Дата перевірки:** 2026-11-11

**Обсяг:** контрактні тести `POST`, `GET`, `PATCH`, `DELETE /api/transactions`

**Рішення:** **GO** — затверджено студенткою 11.11.2026 для поетапної реалізації

Тести повторно звірено із SRS, `AC-003`–`AC-009`, `AC-016`–`AC-021`, `BDD-005`–`BDD-011`, API-сценаріями та `spec/openapi.json`. Покрито структуру `Transaction`/`ErrorResponse`, суми, типи, дати, `X-Client-Local-Date`, Category/type, description, фільтри та їх AND/включні межі, сортування без фіксації порядку однакових дат, частковий PATCH, видалення, 400/404/405/415/422. Кожен case використовує окрему тимчасову SQLite та не залежить від порядку запуску.

Команда:

```powershell
python -m pytest tests/test_transactions_api.py -q --tb=no -p no:cacheprovider
```

Результат після повторного аудиту: **92 collected; 0 PASS; 58 RED; 34 SKIPPED; 1 warning**.

- Початкові **56 RED / 29 SKIPPED** перевірено: очікування коректні, а SKIP обґрунтовані stateful-передумовами. Аудит додав 2 незалежні RED для невідомого/повтореного query parameter та 5 SKIPPED для read-only PATCH-полів, обов’язкового PATCH-header, відсутньої Category і незмінності state після відхиленого POST.
- **58 RED підтверджено студенткою** як коректну вихідну фазу TDD: Category-передумови успішно створюються, але Transaction routes відсутні й повертають `404` замість контрактних відповідей; для 404/405 також відсутній контрактний `ErrorResponse`.
- **34 cases тимчасово SKIPPED:** незмінність state після відхиленого POST, заповнений список, сортування, фільтрація state, успішний і невалідний PATCH зі збереженням попереднього стану, успішний і повторний DELETE. Перед реалізацією кожної відповідної поведінки пов’язані SKIPPED-тести обов’язково активуються, запускаються та перевіряються у фазі RED.
- Category regression: **40 PASS, 1 SKIPPED**; наявний Category-набір не змінено.

Відкладене покриття: `API-P-011` додається після GREEN CRUD, коли одну SQLite можна повторно відкрити новим app instance; `API-N-028` — після реалізації Transaction read/repository та контрактного `DATA_READ_ERROR`; `API-N-029` — після появи контрольованої точки збою перед SQLite commit для POST/PATCH/DELETE. Ці reliability cases виконуються до фінального regression, але не блокують TEST-GATE для початку CRUD. Частина `AC-009` про фінансові показники перевірятиметься у блоці Financial Summary. Warning deprecation FastAPI/Starlette TestClient на RED не впливає.
