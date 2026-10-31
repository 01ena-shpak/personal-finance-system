# Перевірка API-GATE лабораторної №4

**Дата перевірки:** 2026-10-31  
**Обсяг:** REST API contract і Prism mock; без FastAPI, SQLite, бізнес-логіки та Flet-клієнта  
**Рекомендація:** **GO**, з одним пунктом **NEEDS REVIEW** щодо меж Prism  
**Остаточне рішення:** **GO — APPROVED**  
**Дата рішення:** 2026-10-31  
**Рішення ухвалила:** студентка

## 1. Джерела та межі перевірки

Перевірено:

- `spec/srs.md`, `spec/addendum.md`;
- `docs/api-resource-model.md`, `docs/api-operation-contracts.md`, `docs/api-schemas.md`, `docs/api-test-scenarios.md`;
- `spec/openapi.json`;
- `logs/api-validation.md`, `logs/api-mock-startup.md`, `logs/api-mock-tests.md`.

Нижче використано оригінальні 10 критеріїв викладача, надані студенткою для завершення API-GATE. Статуси спираються лише на наявні артефакти й фактичні результати перевірок; тести майбутньої FastAPI/SQLite-реалізації не вважаються передумовою лабораторної №4.

## 2. Результати за 10 критеріями

| № | Оригінальний критерій викладача | Докази | Статус | Обґрунтування |
|---:|---|---|---|---|
| 1 | Кожна суттєва API operation має обґрунтований зв’язок з REQ-ID | `docs/api-resource-model.md`, таблиці операцій і розділ 6; `docs/api-operation-contracts.md`, поле REQ-ID кожної операції; `spec/openapi.json`, `x-req-ids`; `logs/api-validation.md`, розділ 6 | PASS | Усі 9 operations мають точні функціональні та наскрізні REQ-ID. Автоматична структурна перевірка зафіксувала 0 пропущених `REQ-F-001`–`REQ-F-024` і `REQ-NF-001`–`REQ-NF-006`; необґрунтованих operations не виявлено. |
| 2 | Ресурси та термінологія відповідають предметній області та глосарію | `spec/srs.md`, розділи 3 і 6; `spec/glossary.md`; `docs/api-resource-model.md`, розділи 2–5; `docs/api-schemas.md` | PASS | Ресурси Category, Transaction і Financial Summary та поняття Transaction List, Filter, Date Range, income/expense і UAH відповідають SRS і глосарію. Технічні JSON-назви однозначні; нових предметних сутностей не додано. |
| 3 | URI та HTTP-методи використовуються послідовно | `docs/api-resource-model.md`, розділ 7; `docs/api-operation-contracts.md`; `spec/openapi.json` | PASS | Колекції мають `/categories` і `/transactions`, item operations — path ID; створення — POST, читання — GET, часткове редагування — PATCH, видалення — DELETE. Financial Summary подано read-only GET. Усі 9 operations узгоджені між документами. |
| 4 | Для операцій визначені request і response schemas | `docs/api-operation-contracts.md`; `docs/api-schemas.md`, розділи 3–8; `spec/openapi.json`, `components/schemas` і operation request/responses | PASS | Для body-операцій задані create/patch schemas, для успішних відповідей — Category, Transaction, list і FinancialSummary schemas; DELETE має задокументований 204 без body. Параметри, required/nullable, заборона невідомих полів і частковий PATCH формалізовані. |
| 5 | Визначені необхідні HTTP-коди та єдина модель помилок | `docs/api-operation-contracts.md`, розділи 1.1–1.2 і status tables; `docs/api-schemas.md`, розділ 7; `spec/openapi.json`, `ErrorResponse`, `ApiErrorCode` і reusable responses | PASS | Для 9 operations визначені success і relevant 4xx/5xx codes. Контракт має одну `ErrorResponse` із обов’язковими `code` і `message`, умовними `field`/`rule`, узгодженим enum кодів та прикладами. Два runtime body Prism не відповідають цій моделі, але це оцінюється у критерії 10: воно не скасовує факту, що модель у затверджуваному контракті визначена. |
| 6 | Передбачені позитивні й негативні сценарії | `docs/api-test-scenarios.md`, розділи 4–7 | PASS | Підготовлено 11 позитивних і 30 негативних сценаріїв з ID, REQ-ID, method/URI, headers, body, expected status і response structure. Сценарії окремо класифіковані як Prism-checkable, simulation only або такі, що потребують реалізації. |
| 7 | API не розкриває без необхідності деталі внутрішньої реалізації | `docs/api-resource-model.md`, розділ 1; `docs/api-schemas.md`, розділ 7; `spec/openapi.json`; `spec/addendum.md`, розділ 8 | PASS | Контракт оперує предметними ресурсами й стабільними ID, потрібними для зв’язків та item operations. У payload немає SQL, table/column names, filesystem paths, stack traces або FastAPI/sqlite3-specific structures. `DATA_READ_ERROR`/`DATA_WRITE_ERROR` є абстрактними API-кодами та не розкривають SQLite. Технології зафіксовані лише в архітектурному addendum, а не нав’язані клієнтові wire contract. |
| 8 | OpenAPI specification проходить автоматичну валідацію | `spec/openapi.json`; `logs/api-validation.md` | PASS | Redocly CLI 2.72.1 завершив перевірку з 0 errors. Два recommended warnings і один minimal warning задокументовані й обґрунтовані; `$ref`, schemas, examples, operationId та `x-req-ids` додатково перевірені. |
| 9 | Mock API запускається на основі затверджуваної специфікації | `logs/api-mock-startup.md`; `logs/api-mock-tests.md`, розділи 2–3 | PASS | Prism CLI 5.14.2 запущено без серверної реалізації безпосередньо зі `spec/openapi.json`; завантажено 9/9 operations, GET-запит прийнято. Особливість фактичних routes без `/api` задокументована без зміни контракту. |
| 10 | Основні позитивні й негативні сценарії відтворюються через mock API | `logs/api-mock-tests.md`, розділи 4–10; `docs/api-test-scenarios.md` | NEEDS REVIEW | Позитивно охоплено 9/9 operations: 10/10 route/status/schema checks пройшли. У 15 реальних schema/route-негативах status збігся 15/15, але body: 3 PASS, 10 PARTIAL через статичний generic example Prism і 2 FAIL BODY через власні parser/router structures. Stateful, cross-field, persistence, атомарність і SQLite-сценарії правильно позначені NOT TESTABLE WITH MOCK; forced `Prefer` responses — SIMULATION ONLY. Отже, основна маршрутизація й schema validation відтворюються, але точна семантика всіх error bodies і бізнес-правил mock-ом не доведена. |

**Підсумок:** 9 PASS, 0 FAIL, 1 NEEDS REVIEW.

## 3. Аналіз 10 PARTIAL і 2 FAIL BODY

### 10 PARTIAL

До групи входять `API-N-002`, `API-N-004`, `API-N-008`, `API-N-014`, `API-N-017`, `API-N-018`, `API-N-019`, `API-N-022`, `API-N-023`, `API-N-026`.

- У кожному випадку Prism фактично відхилив невалідний request і повернув очікуваний статус `422`.
- OpenAPI містить reusable `422` response з кількома валідними прикладами `ErrorResponse`.
- Prism 5.14.2 вибирає статичний перший приклад (`invalidAmount`) і не синтезує `field`/`rule` із конкретного schema violation. Через це body структурно сумісний з `ErrorResponse`, але семантично не описує фактичну причину.
- Це обмеження генератора mock-відповіді. Ознак помилкового URI, status code, request schema, `$ref` або `ErrorResponse` у специфікації не виявлено.

### 2 FAIL BODY

- `API-N-001`: malformed JSON обробляється JSON parser Prism; отримано його власний `invalid_json`, а не контрактний `ErrorResponse(MALFORMED_JSON)`.
- `API-N-027`: unknown method обробляється router Prism; отримано `application/problem+json` / `NO_METHOD_MATCHED_ERROR`, а не `ErrorResponse(METHOD_NOT_ALLOWED)`.
- Обидва expected HTTP status пройшли (`400` і `405`). Розбіжність виникає до вибору OpenAPI response, тому додавання ще одного example у response не усуне її.

Висновок: 10 PARTIAL і 2 FAIL BODY не доводять дефект `spec/openapi.json`, але й не можуть бути зараховані як повний доказ єдиної error-body поведінки майбутнього FastAPI-сервера.

## 4. Критичні недоліки та мінімальні дії

Критичних недоліків контракту, які вимагали б зміни SRS, BDD або OpenAPI перед API-GATE, не виявлено. Специфікацію навмисно не змінено лише для пристосування до поведінки Prism.

Мінімальні дії в межах лабораторної №4:

1. Під час демонстрації показати один реальний schema-invalid request як доказ request validation і окремо `Prefer: code`/іменований example як доказ наявності задокументованої error response; не називати forced response перевіркою бізнес-правила.
2. Явно пояснити, що parser/router errors Prism не відображають майбутній FastAPI exception handling.
3. Якщо офіційний checklist викладача вимагає, щоб саме Prism динамічно повертав точний `ErrorResponse` для malformed JSON і 405, цей пункт потребує окремого погодження: стандартний Prism mock цього не доводить без власного proxy/реалізації, що виходить за межі лабораторної №4.

Реалізаційні тести FastAPI, SQLite, persistence, атомарності, stateful та cross-field бізнес-правил належать лабораторній №5 і не є блокером поточного API-GATE.

## 5. Рекомендація

Рекомендація — **GO** для завершення API-GATE лабораторної №4: 9 критеріїв виконані, контракт повний, простежуваний, валідований і запускається через mock; нової функціональності поза SRS та витоку зайвих деталей реалізації не виявлено. Один **NEEDS REVIEW** слід прийняти свідомо як межу Prism: mock не доводить точну динамічну семантику всіх error bodies і stateful бізнес-правила. Це не вимагає FastAPI/SQLite-тестів у лабораторній №4. Якщо викладач трактує критерій 10 як обов’язковий буквальний збіг усіх runtime error bodies саме в Prism, рекомендацію слід змінити на **REVISE**; за наявними формулюваннями критичного блокера немає.

## 6. Остаточне рішення студентки

31.10.2026 студентка затвердила рішення **API-GATE: GO** на підставі результату **9 PASS, 0 FAIL, 1 NEEDS REVIEW**.

Студентка прийняла задокументовані обмеження Prism щодо 10 PARTIAL і 2 FAIL BODY. Ці результати не перекласифіковано як повні PASS: точна реалізаційна перевірка єдиної моделі помилок, stateful і cross-field бізнес-правил, persistence, атомарності та SQLite переноситься до лабораторної №5. Обмеження Prism не змінюють контракт і не є блокером API-GATE лабораторної №4.
