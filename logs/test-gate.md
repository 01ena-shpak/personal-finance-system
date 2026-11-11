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
