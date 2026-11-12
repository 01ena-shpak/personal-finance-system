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

## Поетапна реалізація після TEST-GATE GO

- **POST `/api/transactions` — RED (11.11.2026):** 37 активних cases FAIL через відсутність route (`404` замість контрактних `201`, `400`, `404`, `415`, `422`); 2 related cases SKIPPED, оскільки перевіряють state через ще відсутні GET/PATCH. Category-передумови й ізольована SQLite працюють. Реалізацію дозволяє затверджений Transaction TEST-GATE `GO`.
- **POST `/api/transactions` — GREEN:** 37 cases PASS після реалізації API/service/repository, SQLite persistence, validation, Category/type rules та контрактних помилок. Один integrity-case передано до GET-етапу; PATCH security case залишається SKIPPED до PATCH.
- **GET `/api/transactions` — RED:** активовано 7 stateful cases; разом із 12 незалежними cases 19/19 FAIL через відсутність GET route (`405` замість `200`/`422`). POST-передумови, порожня SQLite та negative-write integrity працюють, тому RED належить GET operation.
- **GET `/api/transactions` — GREEN:** 19 cases PASS після реалізації empty/list, strict query validation, AND-фільтрів, включних Date Range і сортування за різними датами від новіших до старіших.
- **PATCH `/api/transactions/{transaction_id}` — RED:** активовано 25 stateful cases; разом із 4 незалежними cases 29/29 FAIL через відсутність PATCH route (`404` замість `200`/`404`/`422`). POST/GET-передумови PASS і підтверджують незмінність state.
- **PATCH `/api/transactions/{transaction_id}` — GREEN:** 29 cases PASS після реалізації atomic partial update, full resulting-state validation, незмінного ID, nullable description, Category/type rules і 404/422.
- **DELETE `/api/transactions/{transaction_id}` — RED:** активовано 2 stateful cases; разом із 5 незалежними cases 7/7 FAIL через відсутність DELETE route та контрактного 405 handler. POST/GET state setup PASS.
- **DELETE `/api/transactions/{transaction_id}` — GREEN:** 7 cases PASS після реалізації atomic delete, повторного DELETE/404, path validation, 204 без body та контрактного 405.
- **CATEGORY_IN_USE — RED:** активовано залежний Category case з ізольованими POST Category/Transaction передумовами; отримано `204` замість `409`, що підтвердило відсутність enforcement foreign key на Category delete connection.
- **CATEGORY_IN_USE — GREEN:** case PASS після ввімкнення SQLite foreign keys на кожному Category connection і мапінгу constraint failure у `409 CATEGORY_IN_USE`.
- **Reliability tests:** підготовлено незалежні `API-P-011`, `API-N-028`, `API-N-029`. `API-P-011` і `API-N-028` одразу PASS на наявній repository-реалізації (restart persistence та `500 DATA_READ_ERROR` уже забезпечені). `API-N-029` підтвердив RED 3/3: контрольований pre-commit hook ігнорувався, тому POST/PATCH/DELETE помилково завершувалися `201`/`200`/`204` замість rollback і `500 DATA_WRITE_ERROR`.
- **Reliability — GREEN:** 5 cases PASS: restart зберігає результат POST/PATCH/DELETE; пошкоджена тестова SQLite повертає `500 DATA_READ_ERROR` без зміни файла; контрольований збій до commit повертає `500 DATA_WRITE_ERROR` і повністю відкочує POST/PATCH/DELETE.
- **Повна Transaction + Category regression:** 138 PASS, 0 FAIL, 0 SKIPPED; 1 TestClient deprecation warning не впливає на поведінку.
- **LOGS:** окремий файловий smoke-check підтвердив `request_started`/`request_finished` і `transaction_created`/`listed`/`updated`/`deleted`; payload, Category name, amount і description до журналу не потрапляють. Тимчасові SQLite/log artifacts після тестів відсутні.

---

# TEST-GATE: Financial Summary API

**Дата перевірки:** 2026-11-12

**Обсяг:** контрактні тести `GET /api/financial-summary`

**Рішення:** **GO** — затверджено студенткою 12.11.2026 після перевірки відповідності специфікації

Підготовлено 5 незалежних cases за `API-P-010`, `REQ-F-002`, `REQ-F-021`–`REQ-F-024`, `AC-022`–`AC-025`, `BDD-012` і `spec/openapi.json`: порожня БД, Total Income/Expenses/Balance, від’ємний баланс, незалежність від Filter, точне десяткове сумування та перерахунок після POST/PATCH/DELETE Transaction. Усі використовують окрему тимчасову SQLite; SKIPPED немає. `API-N-028` і контрактний 405 не дублюються, оскільки вже перевірені незалежними cross-cutting тестами спільних read/error handlers.

Команда:

```powershell
python -m pytest tests/test_financial_summary_api.py -q --tb=line -p no:cacheprovider
```

Результат: **5 collected; 0 PASS; 5 RED; 0 SKIPPED; 1 warning**. Усі cases отримали `404` замість контрактного `200`; Category/Transaction setup та ізольована SQLite працюють, тому RED підтверджує відсутність Financial Summary route, а не помилку тестового середовища.

Category + Transaction regression: **138 PASS, 0 FAIL, 0 SKIPPED; 1 warning**. Warning — наявне TestClient deprecation і на результат не впливає.

Відповідність 5 тестів SRS, Acceptance Criteria та затвердженому OpenAPI підтверджено; студентка затвердила **5 RED** і **138 PASS** регресії як підставу для TEST-GATE `GO`.

---

## REST API refactoring audit — 12.11.2026

- Baseline до рефакторингу: **143 PASS, 0 FAIL, 0 SKIPPED**, 1 TestClient deprecation warning.
- Після рефакторингу: **143 PASS, 0 FAIL, 0 SKIPPED**, те саме warning; зовнішня поведінка не змінилася.
- Перевірено 9/9 операцій: ефективні URI `/api/...`, методи, success/error HTTP-коди, path/query/header parameters, request/response schemas та `ErrorResponse` відповідають затвердженому `spec/openapi.json`; operationId синхронізовано з контрактом.
- Рефакторинг: спільні storage errors винесено з Category service, composition-root змінні уточнено, невикористаний legacy `src/finance.py` видалено.
- Файлове логування та ізоляція SQLite підтверджені; payload і фінансові значення не журналюються, тимчасові test artifacts відсутні.
- Відкрита метаданна розбіжність: автоматично згенерований FastAPI `/openapi.json` не декларує всі error responses і вручну валідовані GET Transaction query parameters, хоча runtime behavior покритий контрактними тестами. Канонічний `spec/openapi.json` не змінено.

---

# TEST-GATE: ADD-L5-F-001 Transaction description search

**Дата перевірки:** 2026-11-12

**Issue:** [#28](https://github.com/01ena-shpak/personal-finance-system/issues/28)

**Рішення:** **GO** — затверджено студенткою 12.11.2026

За затвердженими `spec/addendum-lab5.md` і `spec/openapi.json` додано 14 нових pytest cases: 13 runtime cases для GET `/api/transactions` і 1 generated-OpenAPI case. Покрито Unicode `casefold()` для українського тексту, trim, literal substring, межі 1/255, порожнє, пробільне, 256-символьне й повторене значення, відсутність збігів, `description: null`, AND із чинними Filter та незмінне сортування.

Команди й результати:

```powershell
python -m pytest tests/test_transactions_api.py -q -p no:cacheprovider -k search_transactions --tb=short
# 13 RED, 97 deselected

python -m pytest tests/test_openapi_documentation.py -q -p no:cacheprovider --tb=short
# 2 PASS, 2 RED

python -m pytest -q -p no:cacheprovider --tb=short
# 145 PASS, 15 RED, 0 SKIPPED, 1 warning
```

- 13 runtime cases очікувано отримали `422`: чинний GET parser вважає `search` невідомим параметром і повертає `rule: known_query_parameter_only` замість пошуку або затверджених `non_blank`, `max_length_255`, `single_value`.
- 2 documentation RED підтверджують, що FastAPI `/openapi.json` ще не містить `SearchFilter` і трьох search-specific правил 422. Один із них є новим case, другий — наявною динамічною перевіркою параметрів проти оновленого контракту.
- Усі stateful передумови POST Category/Transaction і тимчасова SQLite працюють; помилок collection, fixtures або тестових очікувань не виявлено.
- Решта 145 tests PASS. Єдине warning — наявне TestClient deprecation; воно не впливає на RED.

Студентка підтвердила **13 RED runtime-тестів**, **2 RED documentation-тести** та **145 PASS регресійних перевірок**. Тести ізольовані, не залежать від порядку; рішення `TEST-GATE: GO` від 12.11.2026 дозволяє переходити до фази GREEN для `ADD-L5-F-001`.
