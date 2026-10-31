# Сценарії тестування REST API Personal Finance System

**Статус:** TEST DESIGN — NOT EXECUTED
**Дата:** 2026-10-31
**Джерела:** SRS, BDD, `docs/api-operation-contracts.md`, `docs/api-schemas.md`, `spec/openapi.json`, `logs/api-mock-startup.md`

## 1. Середовище й межі перевірки

Для Prism CLI 5.14.2 фактична базова адреса mock API:

```text
http://127.0.0.1:4010
```

Prism зареєстрував `paths` без префікса `/api`, тому сценарії mock використовують `/categories`, `/transactions` і `/financial-summary`. Контрактні URI залишаються `/api/...`; ця різниця є особливістю запуску Prism і не змінює API-дизайн.

Класи перевірки:

- **Prism** — можна перевірити маршрут, HTTP-метод, параметри, JSON schema та наявний у OpenAPI приклад відповіді.
- **Prism simulation** — Prism може повернути вибраний задокументований status/example, зокрема через `Prefer: code=<status>`, але це лише імітація відповіді, не доказ бізнес-правила.
- **Implementation** — потрібні реальний state, бізнес-логіка, persistence або SQLite. Такий результат не можна вважати перевіреним через Prism.

Повне тестування цим документом не запускається.

## 2. Позначення структур

### Headers

- `J` = `Content-Type: application/json` або `application/json; charset=utf-8`.
- `D` = `X-Client-Local-Date: 2026-10-31`.
- `—` = спеціальні headers не потрібні.

### Response structures

- `Category` = `{id, name, type}`.
- `CategoryListResponse` = масив `Category`.
- `Transaction` = `{id, type, amount, date, category_id, category_name, description}`.
- `TransactionListResponse` = масив `Transaction`.
- `FinancialSummary` = `{total_income, total_expenses, current_balance}`.
- `ErrorResponse(CODE)` = `{error: {code: CODE, message, field?, rule?}}`.
- `No Content` = порожнє тіло відповіді.

## 3. Передумови stateful-сценаріїв

Ці передумови застосовуються лише до майбутньої Implementation-перевірки:

- Category `1`: `Зарплата`, `income`;
- Category `2`: `Їжа`, `expense`, використовується Transaction `11`;
- Category `3`: `Подорожі`, `expense`, не використовується;
- Transaction `10`: income `25000.00`, дата `2026-10-30`, Category `1`;
- Transaction `11`: expense `850.50`, дата `2026-10-29`, Category `2`.

ID у Prism-прикладах можуть бути іншими; Prism не зберігає цей state.

## 4. Позитивні сценарії

| ID | REQ-ID | Клас | HTTP і фактичний Prism URI | Headers | Request body | Очікуваний результат |
|---|---|---|---|---|---|---|
| `API-P-001` | `REQ-F-001`, `REQ-F-010`, `REQ-F-011`, `REQ-NF-001` | Prism + Implementation | `POST /categories` | `J` | `{"name":"Премія","type":"income"}` | `201`; `Category`, новий додатний незмінний `id`, нормалізовані поля. Prism перевіряє контракт; унікальність і persistence — Implementation. |
| `API-P-002` | `REQ-F-012`, `REQ-NF-003`, `REQ-NF-006` | Prism + Implementation | `GET /categories` | `—` | немає | `200`; `CategoryListResponse`. Implementation повертає фактично збережені Category; порожній state дає `[]`. |
| `API-P-003` | `REQ-F-001`, `REQ-F-011`, `REQ-F-013`, `REQ-NF-001` | Prism + Implementation | `PATCH /categories/2` | `J` | `{"name":"Харчування"}` | `200`; повна `Category` з `id:2`, новою назвою та незмінним `type`. Пов’язані Transaction відображають нову назву лише в Implementation. |
| `API-P-004` | `REQ-F-001`, `REQ-F-014`, `REQ-NF-001` | Prism + Implementation | `DELETE /categories/3` | `—` | немає | `204`; `No Content`. Фактична перевірка відсутності залежностей і видалення — Implementation. |
| `API-P-005` | `REQ-F-001`, `REQ-F-002`, `REQ-F-003`, `REQ-F-004`, `REQ-F-005`, `REQ-F-006`, `REQ-F-007`, `REQ-NF-001` | Prism + Implementation | `POST /transactions` | `J`, `D` | `{"type":"income","amount":"1500.00","date":"2026-10-31","category_id":1,"description":null}` | `201`; `Transaction` із новим незмінним `id`, `category_name:"Зарплата"`. Зв’язок і persistence — Implementation. |
| `API-P-006` | `REQ-F-002`, `REQ-F-015`, `REQ-F-016`, `REQ-F-019`, `REQ-NF-006` | Prism + Implementation | `GET /transactions` | `—` | немає | `200`; `TransactionListResponse`, різні дати від новішої до старішої; `id` передається API, але не показується клієнтом. |
| `API-P-007` | `REQ-F-017`, `REQ-F-020` | Prism + Implementation | `GET /transactions?type=expense&category_id=2&date_from=2026-10-01&date_to=2026-10-31` | `—` | немає | `200`; масив лише Transaction, що відповідають усім Filter; `[]`, якщо збігів немає. Prism перевіряє параметри, але не фільтрує state як бізнес-логіка. |
| `API-P-008` | `REQ-F-001`, `REQ-F-002`, `REQ-F-004`, `REQ-F-005`, `REQ-F-006`, `REQ-F-007`, `REQ-F-008`, `REQ-NF-001` | Prism + Implementation | `PATCH /transactions/10` | `J`, `D` | `{"amount":"27500.00","description":"Зарплата з премією"}` | `200`; повна оновлена `Transaction`, `id:10` незмінний. Атомарне оновлення state — Implementation. |
| `API-P-009` | `REQ-F-001`, `REQ-F-009`, `REQ-NF-001` | Prism + Implementation | `DELETE /transactions/11` | `—` | немає | `204`; `No Content`. В Implementation Transaction зникає зі списку й показників. |
| `API-P-010` | `REQ-F-002`, `REQ-F-021`, `REQ-F-022`, `REQ-F-023`, `REQ-F-024`, `REQ-NF-003`, `REQ-NF-006` | Prism + Implementation | `GET /financial-summary` | `—` | немає | `200`; `FinancialSummary`. Для передумов: `25000.00`, `850.50`, `24149.50`; Filter списку не впливає. Обчислення — лише Implementation. |

## 5. Негативні сценарії контракту й валідації

| ID | REQ-ID | Клас | HTTP і фактичний Prism URI | Headers | Request body / умова | Очікуваний результат |
|---|---|---|---|---|---|---|
| `API-N-001` | `REQ-NF-005` | Prism | `POST /categories` | `J` | обірване JSON: `{"name":"Їжа"` | `400`; `ErrorResponse(MALFORMED_JSON)`. |
| `API-N-002` | `REQ-F-010`, `REQ-NF-005` | Prism | `POST /categories` | `J` | `{"type":"income"}` | `422`; `ErrorResponse(VALIDATION_ERROR)`, `field:"name"`. |
| `API-N-003` | `REQ-F-011`, `REQ-NF-005` | Implementation; Prism simulation only | `POST /categories` | `J` | `{"name":"   ","type":"income"}` | `422`; `ErrorResponse(VALIDATION_ERROR)`. Trim робить значення порожнім; OpenAPI schema не може виразити довжину після нормалізації, тому Prism не доводить це правило. |
| `API-N-004` | `REQ-F-011`, `REQ-NF-005` | Prism | `POST /categories` | `J` | `{"name":"Премія","type":"other"}` | `422`; `ErrorResponse(VALIDATION_ERROR)`, правило enum. |
| `API-N-005` | `REQ-F-011` | Implementation; Prism simulation only | `POST /categories` | `J` | наявна `Зарплата/income`; body `{"name":"  зарплата  ","type":"income"}` | `409`; `ErrorResponse(CATEGORY_NAME_CONFLICT)`. Prism може лише зімітувати 409, але не перевіряє case-insensitive uniqueness після trim. |
| `API-N-006` | `REQ-NF-005` | Prism | `POST /categories` | `Content-Type: text/plain` | валідний JSON-текст | `415`; `ErrorResponse(UNSUPPORTED_MEDIA_TYPE)`. |
| `API-N-007` | `REQ-F-013` | Implementation; Prism simulation only | `PATCH /categories/999` | `J` | `{"name":"Нова назва"}` | `404`; `ErrorResponse(RESOURCE_NOT_FOUND)`. Prism не має state для доказу відсутності ID. |
| `API-N-008` | `REQ-F-013`, `REQ-NF-005` | Prism | `PATCH /categories/2` | `J` | `{}` або `{"type":"income"}` | `422`; `ErrorResponse(VALIDATION_ERROR)` через відсутнє `name` або невідоме поле. |
| `API-N-009` | `REQ-F-014` | Implementation; Prism simulation only | `DELETE /categories/2` | `—` | Category використовується Transaction `11` | `409`; `ErrorResponse(CATEGORY_IN_USE)`; Category і Transaction не змінені. |
| `API-N-010` | `REQ-F-014` | Implementation; Prism simulation only | `DELETE /categories/999` | `—` | ресурсу немає | `404`; `ErrorResponse(RESOURCE_NOT_FOUND)`. |
| `API-N-011` | `REQ-F-004`, `REQ-NF-005` | Prism | `POST /transactions` | `J`, `D` | `{"type":"income","amount":1250.0,"date":"2026-10-30","category_id":1}` | `422`; `ErrorResponse(VALIDATION_ERROR)`, `field:"amount"`; number не приймається замість decimal string. |
| `API-N-012` | `REQ-F-004`, `REQ-NF-005` | Prism | `POST /transactions` | `J`, `D` | `{"type":"income","amount":"0.00","date":"2026-10-30","category_id":1}` | `422`; `ErrorResponse(VALIDATION_ERROR)`, сума повинна бути додатною. |
| `API-N-013` | `REQ-F-005`, `REQ-NF-005` | Implementation; Prism simulation only | `POST /transactions` | `J`, `X-Client-Local-Date: 2026-10-31` | `{"type":"income","amount":"1.00","date":"2026-11-01","category_id":1}` | `422`; `ErrorResponse(VALIDATION_ERROR)`, `rule:"not_after_client_local_date"`. Cross-field date rule не доводиться Prism. |
| `API-N-014` | `REQ-F-005`, `REQ-NF-005` | Prism | `POST /transactions` | лише `J` | валідний `TransactionCreate` без `X-Client-Local-Date` | `422`; `ErrorResponse(VALIDATION_ERROR)` для header. |
| `API-N-015` | `REQ-F-007`, `REQ-NF-005` | Implementation; Prism simulation only | `POST /transactions` | `J`, `D` | `{"type":"income","amount":"1.00","date":"2026-10-31","category_id":2}` | `422`; `ErrorResponse(VALIDATION_ERROR)`, `rule:"category_type_matches_transaction_type"`. |
| `API-N-016` | `REQ-F-007` | Implementation; Prism simulation only | `POST /transactions` | `J`, `D` | `category_id:999` у решті валідного body | `404`; `ErrorResponse(RESOURCE_NOT_FOUND)`. |
| `API-N-017` | `REQ-F-006`, `REQ-NF-005` | Prism | `POST /transactions` | `J`, `D` | `description` довжиною 256 символів | `422`; `ErrorResponse(VALIDATION_ERROR)`, `field:"description"`. |
| `API-N-018` | `REQ-NF-004`, `REQ-NF-005` | Prism | `POST /transactions` | `J`, `D` | валідні поля плюс невідоме `command` | `422`; `ErrorResponse(VALIDATION_ERROR)` через `additionalProperties:false`; текст у дозволеному Description не виконується лише в Implementation. |
| `API-N-019` | `REQ-F-017`, `REQ-NF-005` | Prism | `GET /transactions?type=other` | `—` | некоректний enum query | `422`; `ErrorResponse(VALIDATION_ERROR)`, `field:"type"`. |
| `API-N-020` | `REQ-F-018`, `REQ-NF-005` | Implementation; Prism simulation only | `GET /transactions?date_from=2026-10-31&date_to=2026-10-01` | `—` | початок після кінця | `422`; `ErrorResponse(VALIDATION_ERROR)`, `field:"date_range"`; Filter не застосовується. OpenAPI описує, але не виражає порівняння дат. |
| `API-N-021` | `REQ-F-017`, `REQ-F-018`, `REQ-NF-005` | Implementation; Prism simulation only | `GET /transactions?date_from=2026-10-01` | `—` | відсутня `date_to` | `422`; `ErrorResponse(VALIDATION_ERROR)`; парність меж не повністю виражена OpenAPI 3.0.3. |
| `API-N-022` | `REQ-F-008`, `REQ-NF-005` | Prism | `PATCH /transactions/10` | `J`, `D` | `{}` | `422`; `ErrorResponse(VALIDATION_ERROR)` через `minProperties:1`; state не змінений в Implementation. |
| `API-N-023` | `REQ-F-004`, `REQ-F-008`, `REQ-NF-005` | Prism | `PATCH /transactions/10` | `J`, `D` | `{"amount":null}` | `422`; `ErrorResponse(VALIDATION_ERROR)`; `null` дозволений лише для Description. |
| `API-N-024` | `REQ-F-008` | Implementation; Prism simulation only | `PATCH /transactions/999` | `J`, `D` | `{"amount":"10.00"}` | `404`; `ErrorResponse(RESOURCE_NOT_FOUND)`. |
| `API-N-025` | `REQ-F-009` | Implementation; Prism simulation only | `DELETE /transactions/999` | `—` | ресурсу немає | `404`; `ErrorResponse(RESOURCE_NOT_FOUND)`. |
| `API-N-026` | `REQ-F-014` або `REQ-F-009`, `REQ-NF-005` | Prism | `DELETE /categories/0` або `DELETE /transactions/0` | `—` | path ID менше minimum `1` | `422`; `ErrorResponse(VALIDATION_ERROR)` для path parameter. |
| `API-N-027` | контракт операцій | Prism | `PUT /categories/1` | за потреби `J` | будь-яке | `405`; `ErrorResponse(METHOD_NOT_ALLOWED)`. |

## 6. Додаткові сценарії надійності, persistence й безпеки

Ці сценарії потребують Implementation і не можуть отримати PASS на підставі mock-відповіді. `API-P-011` є позитивною перевіркою persistence; решта сценаріїв у секції — негативні або захисні.

| ID | REQ-ID | Клас | HTTP і URI | Headers | Умова / body | Очікуваний результат |
|---|---|---|---|---|---|---|
| `API-N-028` | `REQ-NF-003` | Implementation only | `GET /categories`, `GET /transactions` або `GET /financial-summary` | `—` | серверу надано окрему нечитабельну тестову SQLite | `500`; `ErrorResponse(DATA_READ_ERROR)`; база не змінена. Prism може показати приклад 500, але не перевіряє SQLite. |
| `API-P-011` | `REQ-F-001`, `REQ-NF-001` | Implementation only | будь-який успішний `POST`/`PATCH`/`DELETE`, потім штатний restart | залежно від operation | валідна зміна | Після restart наступний GET показує повний успішно збережений результат. Prism не має persistence. |
| `API-N-029` | `REQ-NF-002` | Implementation only | будь-який `POST`/`PATCH`/`DELETE` | залежно від operation | контрольована помилка до commit | `500`; `ErrorResponse(DATA_WRITE_ERROR)`; попередній стан повністю збережений, часткових змін немає. |
| `API-N-030` | `REQ-NF-004` | Implementation only | `POST /categories` або `POST/PATCH /transactions` | `J`, для Transaction також `D` | синтаксис команд або коду в `name`/`description`, який виконує інші правила поля | Значення зберігається/повертається як текст і не виконується. Prism перевіряє лише string schema, а не безпечність виконання. |

## 7. Матриця покриття operations

| Operation | Позитивні ID | Основні негативні ID |
|---|---|---|
| `POST /categories` | `API-P-001`, `API-P-011` | `API-N-001`–`API-N-006`, `API-N-029`, `API-N-030` |
| `GET /categories` | `API-P-002` | `API-N-028` |
| `PATCH /categories/{category_id}` | `API-P-003`, `API-P-011` | `API-N-007`, `API-N-008`, `API-N-029` |
| `DELETE /categories/{category_id}` | `API-P-004`, `API-P-011` | `API-N-009`, `API-N-010`, `API-N-026`, `API-N-029` |
| `POST /transactions` | `API-P-005`, `API-P-011` | `API-N-011`–`API-N-018`, `API-N-029`, `API-N-030` |
| `GET /transactions` | `API-P-006`, `API-P-007` | `API-N-019`–`API-N-021`, `API-N-028` |
| `PATCH /transactions/{transaction_id}` | `API-P-008`, `API-P-011` | `API-N-022`–`API-N-024`, `API-N-029`, `API-N-030` |
| `DELETE /transactions/{transaction_id}` | `API-P-009`, `API-P-011` | `API-N-025`, `API-N-026`, `API-N-029` |
| `GET /financial-summary` | `API-P-010` | `API-N-028` |

## 8. Підсумок покриття

- Позитивних сценаріїв: 11.
- Негативних сценаріїв: 30.
- Покрито operations: 9 із 9.
- Покрито функціональні вимоги API: `REQ-F-001`–`REQ-F-024`.
- Покрито наскрізні вимоги: `REQ-NF-001`–`REQ-NF-006`.
- Prism придатний для route/schema/example перевірок, але не доводить persistence, унікальність, наявність ресурсів, зв’язки Category–Transaction, фільтрацію state, фінансові обчислення, атомарність або поведінку SQLite.
