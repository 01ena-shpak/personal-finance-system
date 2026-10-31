# Фактична перевірка Prism mock API

**Дата:** 2026-10-31
**Специфікація:** `spec/openapi.json`
**Prism CLI:** `5.14.2`
**Адреса під час тесту:** `http://127.0.0.1:4010`
**Підсумок mock-рівня:** PASS WITH LIMITATIONS

## 1. Підготовка тест-дизайну

Перед запуском у `docs/api-test-scenarios.md`:

- заголовок секції 6 змінено на «Додаткові сценарії надійності, persistence й безпеки»;
- відновлено безперервну негативну нумерацію `API-N-001`–`API-N-030`;
- колишні `API-N-030` і `API-N-031` перенумеровано на `API-N-029` і `API-N-030`;
- усі посилання в матриці покриття оновлено;
- збережено 11 позитивних і 30 негативних сценаріїв.

## 2. Фактично виконані команди

Запуск:

```powershell
npx --yes @stoplight/prism-cli@5.14.2 mock spec/openapi.json -p 4010
```

HTTP-запити виконано PowerShell harness на основі `System.Net.Http.HttpClient` без proxy. Для кожного рядка таблиць нижче фактично створювався `HttpRequestMessage` із указаними method, URI, headers і body, після чого фіксувалися status, response `Content-Type` і повне body:

```powershell
Add-Type -AssemblyName System.Net.Http
$handler = New-Object System.Net.Http.HttpClientHandler
$handler.UseProxy = $false
$client = New-Object System.Net.Http.HttpClient($handler)
$response = $client.SendAsync($request).Result
$status = [int]$response.StatusCode
$body = $response.Content.ReadAsStringAsync().Result
```

Для simulation-запитів додано:

```powershell
$request.Headers.TryAddWithoutValidation("Prefer", "code=<status>")
```

Зупинка після тестів:

```text
Ctrl+C
```

Після зупинки `Get-NetTCPConnection -LocalPort 4010 -State Listen` не знайшов listener: порт 4010 звільнено.

## 3. Завантаження operations

Prism зареєстрував усі 9 operations без server prefix `/api`:

- `POST`, `GET /categories`;
- `PATCH`, `DELETE /categories/{category_id}`;
- `POST`, `GET /transactions`;
- `PATCH`, `DELETE /transactions/{transaction_id}`;
- `GET /financial-summary`.

Це відповідає раніше зафіксованій поведінці Prism 5.14.2. OpenAPI-контракт не змінювався.

## 4. Позитивні mock-перевірки

`PASS (mock contract)` означає: маршрут прийнято, status відповідає OpenAPI, а body відповідає задокументованій JSON-структурі або є порожнім для 204. Це не доказ state чи бізнес-логіки.

| Scenario | Фактичний запит | Очікувано | Фактично | Response body check | Результат |
|---|---|---:|---:|---|---|
| `API-P-001` | `POST /categories`, JSON `Премія/income`, `application/json; charset=utf-8` | 201 | 201 | Валідний `Category`; Prism повернув статичний приклад `Зарплата`, не echo request. | PASS (mock contract) |
| `API-P-002` | `GET /categories` | 200 | 200 | Валідний `CategoryListResponse` із двох елементів. | PASS (mock contract) |
| `API-P-003` | `PATCH /categories/2`, `{"name":"Харчування"}` | 200 | 200 | Валідний `Category`, `id:2`, `type:expense`. | PASS (mock contract) |
| `API-P-004` | `DELETE /categories/3` | 204 | 204 | Body порожнє. Prism вказав `text/plain`, але для 204 content не визначений і body відсутнє. | PASS (mock contract) |
| `API-P-005` | `POST /transactions` із валідним body та `X-Client-Local-Date` | 201 | 201 | Валідний `Transaction`; статичний приклад, не результат збереження request. | PASS (mock contract) |
| `API-P-006` | `GET /transactions` | 200 | 200 | Валідний `TransactionListResponse`. | PASS (mock contract) |
| `API-P-007` | `GET /transactions?type=expense&category_id=2&date_from=2026-10-01&date_to=2026-10-31` | 200 | 200 | Schema валідна, але повернуто income-приклад, що не відповідає Filter. Фільтрація не є можливістю mock. | PASS route/schema; semantics NOT TESTABLE |
| `API-P-008` | `PATCH /transactions/10` із amount/description та required header | 200 | 200 | Валідний повний `Transaction`. | PASS (mock contract) |
| `API-P-009` | `DELETE /transactions/11` | 204 | 204 | Body порожнє. | PASS (mock contract) |
| `API-P-010` | `GET /financial-summary` | 200 | 200 | `{"total_income":"25000.00","total_expenses":"850.50","current_balance":"24149.50"}` відповідає `FinancialSummary`. | PASS (mock contract) |

`API-P-011` (persistence після restart) — **NOT TESTABLE WITH MOCK**.

## 5. Реальні невалідні запити до Prism

Ці запити були невалідними за OpenAPI schema або route/method. `PARTIAL` означає, що status правильний і body є JSON, але конкретна помилка не відповідає причині запиту. `FAIL BODY` означає, що Prism повернув власну структуру замість погодженої `ErrorResponse`.

| Scenario | Фактичний запит / порушення | Очікувано | Фактично | Фактична перевірка body | Результат |
|---|---|---:|---:|---|---|
| `API-N-001` | `POST /categories`, обірваний JSON | 400 | 400 | Prism: `{"error":{"code":"invalid_json","message":"Invalid JSON"}}`; code не входить до `ApiErrorCode`, немає погодженого формату поля/rule. | FAIL BODY; status PASS |
| `API-N-002` | `POST /categories`, відсутнє `name` | 422 | 422 | `ErrorResponse`, але приклад помилково вказує `field:amount`. | PARTIAL |
| `API-N-004` | `POST /categories`, `type:other` | 422 | 422 | `ErrorResponse`, але повернуто generic `invalidAmount` example. | PARTIAL |
| `API-N-006` | `POST /categories`, `Content-Type:text/plain` | 415 | 415 | Повний погоджений `ErrorResponse(UNSUPPORTED_MEDIA_TYPE)`. | PASS |
| `API-N-008` | `PATCH /categories/2`, `{}` і окремо body з невідомим `type` | 422 | 422 | Обидва запити відхилені; body — generic `invalidAmount`, не причина CategoryPatch. | PARTIAL |
| `API-N-011` | `amount` як JSON number | 422 | 422 | `ErrorResponse(VALIDATION_ERROR)` для `amount`. | PASS |
| `API-N-012` | `amount:"0.00"` | 422 | 422 | `ErrorResponse(VALIDATION_ERROR)` для додатної суми. | PASS |
| `API-N-014` | відсутній `X-Client-Local-Date` | 422 | 422 | Status правильний; body помилково посилається на `amount`. | PARTIAL |
| `API-N-017` | Description 256 символів | 422 | 422 | Status правильний; body помилково посилається на `amount`. | PARTIAL |
| `API-N-018` | невідоме поле `command` | 422 | 422 | Status правильний; body помилково посилається на `amount`. | PARTIAL |
| `API-N-019` | query `type=other` | 422 | 422 | Status правильний; body помилково посилається на `amount`. | PARTIAL |
| `API-N-022` | порожній TransactionPatch | 422 | 422 | Status правильний; generic `invalidAmount` example. | PARTIAL |
| `API-N-023` | `amount:null` | 422 | 422 | Status правильний; body про amount, але не уточнює заборону null. | PARTIAL |
| `API-N-026` | окремо `DELETE /categories/0` і `/transactions/0` | 422 | 422 | Обидва minimum-порушення відхилені; body помилково посилається на `amount`. | PARTIAL |
| `API-N-027` | `PUT /categories/1` | 405 | 405 | Prism повернув `application/problem+json` з `NO_METHOD_MATCHED_ERROR`, не `ErrorResponse(METHOD_NOT_ALLOWED)`. | FAIL BODY; status PASS |

Підсумок цієї групи за scenario ID:

- перевірено: 15;
- очікуваний HTTP status отримано: 15/15;
- повний PASS status + очікувана ErrorResponse семантика: 3;
- PARTIAL через generic невідповідний error example: 10;
- FAIL BODY через власну Prism error structure: 2.

## 6. Raw probes бізнес-правил

Ці запити виконано без `Prefer`. Вони показують, що schema-valid request Prism приймає незалежно від state або міжпольового правила. Розбіжність status тут не є дефектом OpenAPI: це доказ **NOT TESTABLE WITH MOCK**.

| Scenario | Запит | Очікування реальної Implementation | Фактичний Prism status | Класифікація |
|---|---|---:|---:|---|
| `API-N-003` | Category Name лише з пробілів | 422 | 201 | NOT TESTABLE WITH MOCK |
| `API-N-005` | дублікат Category після trim/case-fold | 409 | 201 | NOT TESTABLE WITH MOCK |
| `API-N-007` | `PATCH /categories/999` | 404 | 200 | NOT TESTABLE WITH MOCK |
| `API-N-009` | видалення використаної Category | 409 | 204 | NOT TESTABLE WITH MOCK |
| `API-N-010` | `DELETE /categories/999` | 404 | 204 | NOT TESTABLE WITH MOCK |
| `API-N-013` | Transaction date пізніша за client-local date | 422 | 201 | NOT TESTABLE WITH MOCK |
| `API-N-015` | невідповідність Transaction/Category type | 422 | 201 | NOT TESTABLE WITH MOCK |
| `API-N-016` | неіснуючий `category_id` | 404 | 201 | NOT TESTABLE WITH MOCK |
| `API-N-020` | `date_from > date_to` | 422 | 200 | NOT TESTABLE WITH MOCK |
| `API-N-021` | лише одна межа Date Range | 422 | 200 | NOT TESTABLE WITH MOCK |
| `API-N-024` | `PATCH /transactions/999` | 404 | 200 | NOT TESTABLE WITH MOCK |
| `API-N-025` | `DELETE /transactions/999` | 404 | 204 | NOT TESTABLE WITH MOCK |

## 7. Примусове відтворення через `Prefer: code`

Ці результати підтверджують лише наявність response status/example у специфікації. Вони не є PASS бізнес-правила.

| Scenario | Prefer | Фактичний status | Фактичне body | Результат |
|---|---:|---:|---|---|
| `API-N-003` | 422 | 422 | generic `ErrorResponse(VALIDATION_ERROR)` для amount | SIMULATION ONLY; body не про trim |
| `API-N-005` | 409 | 409 | `CATEGORY_NAME_CONFLICT` із name/rule | SIMULATION ONLY |
| `API-N-009` | 409 | 409 | `CATEGORY_IN_USE` | SIMULATION ONLY |
| `API-N-013` | 422 | 422 | generic validation для amount | SIMULATION ONLY; body не про date |
| `API-N-020` | 422 | 422 | generic validation для amount | SIMULATION ONLY; body не про Date Range |
| `API-N-024` | 404 | 404 | `RESOURCE_NOT_FOUND` | SIMULATION ONLY |
| `API-N-028` | 500 | 500 | `DATA_READ_ERROR` | SIMULATION ONLY; SQLite не читалася |
| `API-N-029` | 500 | 500 | перший 500 example `DATA_READ_ERROR`, а не очікуваний `DATA_WRITE_ERROR` | SIMULATION ONLY; атомарність не перевірена |

## 8. Сценарії без фактичної mock-перевірки бізнес-результату

- `API-P-011`: persistence після restart.
- `API-N-003`, `005`, `007`, `009`, `010`, `013`, `015`, `016`, `020`, `021`, `024`, `025`: виконані probes підтвердили відсутність бізнес-логіки в Prism.
- `API-N-028`: нечитабельна SQLite; лише simulation 500.
- `API-N-029`: перервана операція/rollback; лише simulation 500.
- `API-N-030`: безпечне невиконання тексту; потребує реалізації.

Усі вони мають остаточний статус **NOT TESTABLE WITH MOCK**, незалежно від наявності forced response.

## 9. Аналіз розбіжностей і OpenAPI

Реальної помилки в `spec/openapi.json` не виявлено:

- маршрути, методи, параметри, required headers, patterns, `additionalProperties:false`, `minProperties` і status codes працюють на mock-рівні;
- generic 422 body виникає тому, що reusable response має кілька examples, а Prism 5.14.2 вибирає перший example, не зіставляючи його з конкретним violation;
- malformed JSON і unknown method обробляються внутрішнім middleware/router Prism до вибору OpenAPI response, тому повертаються власні Prism structures;
- stateful і cross-field правила навмисно задокументовані в `description`, бо їх не можна повністю виразити схемами OpenAPI 3.0.3.

Через відсутність дефекту специфікації `spec/openapi.json` не змінювався, повторний Redocly lint не був потрібний.

## 10. Статистика й висновок

- Operations, фактично охоплені позитивними запитами: 9/9.
- Позитивні mock-сценарії виконано: 10; status/schema PASS: 10.
- Позитивний persistence-сценарій: 1 NOT TESTABLE WITH MOCK.
- Реальні schema/route-негативи: 15; status PASS 15, повний body PASS 3, PARTIAL 10, FAIL BODY 2.
- Raw business probes: 12; усі NOT TESTABLE WITH MOCK.
- Forced response simulations: 8; усі SIMULATION ONLY.
- Implementation-only негативні сценарії загалом: 15, включно з probes/simulations; жоден не позначено PASS за mock.
- Prism зупинено; порт 4010 звільнено.

Mock-контракт готовий як доказ маршрутизації, schema validation, status negotiation і позитивних response examples. Реалізаційні тести бізнес-правил, persistence, SQLite, атомарності та динамічної генерації `ErrorResponse` за фактичною причиною помилки належать лабораторній №5 і не є передумовою API-GATE лабораторної №4. У межах API-GATE підлягають оцінюванню повнота й узгодженість контракту, валідність OpenAPI та чесно задокументовані можливості й обмеження mock API; розбіжності Prism щодо error body залишаються предметом ручного перегляду, а не доказом реалізаційної поведінки.
