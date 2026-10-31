# Формальні схеми REST API Personal Finance System

**Статус:** DESIGN FOR MOCK API
**Дата:** 2026-10-31
**Пов’язані документи:** `docs/api-resource-model.md`, `docs/api-operation-contracts.md`

## 1. Правила опису схем

Цей документ формалізує JSON-структури погодженого контракту, але не є OpenAPI або окремим JSON Schema-файлом.

- У кожній об’єктній схемі невідомі поля заборонені (`additional properties: false`).
- «Обов’язкове» означає, що ключ повинен бути присутнім у JSON-об’єкті.
- «Nullable» означає, що явне JSON-значення `null` дозволене. Необов’язкове поле й nullable-поле — різні поняття.
- Рядки не перетворюються автоматично з чисел, boolean або інших JSON-типів.
- Ідентифікатори не змінюються після створення.
- У request-схемах серверні поля `id` і `category_name` заборонені.
- Усі правила між полями перевіряються після перевірки окремих полів.

## 2. Спільні типи й обмеження

| Тип | JSON-тип | Nullable | Формат та обмеження |
|---|---|---:|---|
| `PositiveId` | integer | ні | `>= 1`; boolean не вважається integer. |
| `TransactionType` | string | ні | Enum: `income`, `expense`. |
| `Amount` | string | ні | Шаблон `^(?!0\.00$)(?:0\|[1-9][0-9]*)\.[0-9]{2}$`; десяткове значення строго більше `0.00`; UAH. |
| `NonNegativeMoney` | string | ні | Шаблон `^(?:0\|[1-9][0-9]*)\.[0-9]{2}$`; значення `>= 0.00`; UAH. |
| `SignedMoney` | string | ні | Шаблон `^(?!-0\.00$)-?(?:0\|[1-9][0-9]*)\.[0-9]{2}$`; може бути від’ємним; нуль нормалізується як `"0.00"`, не `"-0.00"`. |
| `LocalDate` | string | ні | Рівно `YYYY-MM-DD`; дата повинна реально існувати. |
| `CategoryNameInput` | string | ні | Після видалення початкових і кінцевих пробілів: довжина `1..50`; унікальність без урахування регістру в межах Category `type`. Зберігається нормалізоване значення. |
| `CategoryName` | string | ні | Нормалізована непорожня назва довжиною до 50 символів. |
| `Description` | string | так | Якщо не `null`, довжина `0..255`; обробляється лише як текстові дані. |

Шаблон перевіряє канонічне JSON-представлення суми з двома цифрами після крапки. Математичні обчислення не повинні використовувати двійкову floating-point арифметику як джерело фінансового результату.

## 3. Category schemas

### 3.1 `Category`

Повне серверне представлення Category.

| Поле | Тип | Обов’язкове | Nullable | Правила |
|---|---|---:|---:|---|
| `id` | `PositiveId` | так | ні | Унікальний незмінний Category ID. |
| `name` | `CategoryName` | так | ні | Нормалізована Category Name. |
| `type` | `TransactionType` | так | ні | Тип Category. |

```json
{
  "id": 2,
  "name": "Їжа",
  "type": "expense"
}
```

### 3.2 `CategoryCreate`

Request body для `POST /api/categories`.

| Поле | Тип | Обов’язкове | Nullable | Правила |
|---|---|---:|---:|---|
| `name` | `CategoryNameInput` | так | ні | Нормалізується перед перевіркою і збереженням. |
| `type` | `TransactionType` | так | ні | Визначає область унікальності назви. |

### 3.3 `CategoryPatch`

Request body для `PATCH /api/categories/{category_id}`.

| Поле | Тип | Обов’язкове | Nullable | Правила |
|---|---|---:|---:|---|
| `name` | `CategoryNameInput` | так | ні | Єдине дозволене поле; перевіряється в межах незмінного типу Category. |

Для цієї PATCH-операції частковість означає, що змінюється лише `name`, а `id` і `type` не входять до body. Порожній об’єкт заборонений.

### 3.4 `CategoryListResponse`

JSON-масив елементів `Category`; мінімальна довжина `0`. Додатковий envelope і pagination відсутні.

```json
[
  {"id": 1, "name": "Зарплата", "type": "income"},
  {"id": 2, "name": "Їжа", "type": "expense"}
]
```

### 3.5 Category response aliases

- `CategoryCreateResponse` = `Category`.
- `CategoryPatchResponse` = `Category`.
- Успішний `DELETE /api/categories/{category_id}` має `204 No Content` і не має JSON-схеми відповіді.

## 4. Transaction schemas

### 4.1 `Transaction`

Повне серверне представлення Transaction. Flet-клієнт використовує `id` для PATCH/DELETE, але не показує його у Transaction List.

| Поле | Тип | Обов’язкове | Nullable | Правила |
|---|---|---:|---:|---|
| `id` | `PositiveId` | так | ні | Унікальний незмінний Transaction ID. |
| `type` | `TransactionType` | так | ні | Тип Transaction. |
| `amount` | `Amount` | так | ні | Додатна сума UAH. |
| `date` | `LocalDate` | так | ні | Дата Transaction. |
| `category_id` | `PositiveId` | так | ні | ID наявної Category відповідного типу. |
| `category_name` | `CategoryName` | так | ні | Поточна назва пов’язаної Category; серверне read-only поле. |
| `description` | `Description` | так | так | Рядок або `null`; у response ключ завжди присутній. |

```json
{
  "id": 10,
  "type": "income",
  "amount": "25000.00",
  "date": "2026-10-30",
  "category_id": 1,
  "category_name": "Зарплата",
  "description": null
}
```

### 4.2 `TransactionCreate`

Request body для `POST /api/transactions`.

| Поле | Тип | Обов’язкове | Nullable | Правила |
|---|---|---:|---:|---|
| `type` | `TransactionType` | так | ні | `income` або `expense`. |
| `amount` | `Amount` | так | ні | Строго додатна сума. |
| `date` | `LocalDate` | так | ні | Не пізніша за дату заголовка `X-Client-Local-Date`. |
| `category_id` | `PositiveId` | так | ні | Category повинна існувати, а її `type` — збігатися з Transaction `type`. |
| `description` | `Description` | ні | так | Пропущене поле або `null` означає відсутність Description. |

Міжпольові правила:

1. `date <= X-Client-Local-Date`.
2. `Category.type == Transaction.type`.
3. `X-Client-Local-Date` є обов’язковим валідним header parameter, але не входить до JSON body.

### 4.3 `TransactionPatch`

Request body для `PATCH /api/transactions/{transaction_id}`.

| Поле | Тип | Обов’язкове окремо | Nullable | Правила |
|---|---|---:|---:|---|
| `type` | `TransactionType` | ні | ні | Якщо присутнє, замінює поточний тип. |
| `amount` | `Amount` | ні | ні | Якщо присутнє, замінює поточну суму. |
| `date` | `LocalDate` | ні | ні | Якщо присутнє, не пізніше `X-Client-Local-Date`. |
| `category_id` | `PositiveId` | ні | ні | Якщо присутнє, Category повинна існувати. |
| `description` | `Description` | ні | так | Рядок замінює Description; `null` видаляє Description. |

Правила часткового PATCH:

- об’єкт містить щонайменше одне з п’яти дозволених полів (`min properties: 1`);
- пропущене поле зберігає поточне значення;
- `null` заборонений для всіх полів, крім `description`;
- після накладання patch перевіряється повний результуючий стан за правилами `TransactionCreate`;
- одночасна зміна `type` і `category_id` дозволена, якщо результуючі типи збігаються;
- `X-Client-Local-Date` обов’язковий для операції незалежно від набору полів;
- за будь-якої помилки початковий стан Transaction не змінюється.

### 4.4 `TransactionListResponse`

JSON-масив елементів `Transaction`; мінімальна довжина `0`. Додатковий envelope і pagination відсутні. Елементи з різними датами впорядковані від новішої дати до старішої; порядок однакових дат не визначений.

```json
[
  {
    "id": 10,
    "type": "income",
    "amount": "25000.00",
    "date": "2026-10-30",
    "category_id": 1,
    "category_name": "Зарплата",
    "description": null
  }
]
```

### 4.5 Transaction response aliases

- `TransactionCreateResponse` = `Transaction`.
- `TransactionPatchResponse` = `Transaction`.
- Успішний `DELETE /api/transactions/{transaction_id}` має `204 No Content` і не має JSON-схеми відповіді.

## 5. `FinancialSummary`

Read-only response для `GET /api/financial-summary`.

| Поле | Тип | Обов’язкове | Nullable | Правила |
|---|---|---:|---:|---|
| `total_income` | `NonNegativeMoney` | так | ні | Сума `amount` усіх Transaction типу `income`. |
| `total_expenses` | `NonNegativeMoney` | так | ні | Сума `amount` усіх Transaction типу `expense`. |
| `current_balance` | `SignedMoney` | так | ні | `total_income - total_expenses`; може бути від’ємним. |

Операція не приймає Filter. Усі показники обчислюються за всіма збереженими Transaction. За відсутності Transaction кожне поле дорівнює `"0.00"`.

```json
{
  "total_income": "25000.00",
  "total_expenses": "850.50",
  "current_balance": "24149.50"
}
```

`FinancialSummaryResponse` = `FinancialSummary`.

## 6. Query і header parameter schemas

### 6.1 `TransactionFilterQuery`

| Параметр | Тип | Обов’язковий | Nullable | Правила |
|---|---|---:|---:|---|
| `type` | `TransactionType` | ні | ні | Filter за Transaction Type. |
| `category_id` | `PositiveId` | ні | ні | Неіснуючий, але коректний ID дає порожній список. |
| `date_from` | `LocalDate` | ні | ні | Передається тільки разом із `date_to`; включна межа. |
| `date_to` | `LocalDate` | ні | ні | Передається тільки разом із `date_from`; включна межа. |

Кілька Filter поєднуються через AND. Якщо Date Range задано, `date_from <= date_to`. Повторення одного query parameter або невідомий query parameter відхиляється як `VALIDATION_ERROR`, щоб контракт залишався однозначним.

### 6.2 `ClientLocalDateHeader`

`X-Client-Local-Date` має тип `LocalDate`, не nullable й обов’язковий для `POST /api/transactions` і `PATCH /api/transactions/{transaction_id}`. Значення відображає поточну локальну дату пристрою User і використовується лише для перевірки `REQ-F-005`.

### 6.3 `JsonContentTypeHeader`

Для операцій із request body `Content-Type` обов’язковий. Медіатип повинен бути `application/json`; дозволені синтаксично коректні параметри медіатипу, наприклад `application/json; charset=utf-8`. Регістр токенів медіатипу порівнюється за правилами HTTP, а не буквальним порівнянням усього рядка. Інший медіатип або некоректні параметри дають `UNSUPPORTED_MEDIA_TYPE`.

## 7. Єдина модель помилки

### 7.1 `ErrorDetail`

| Поле | Тип | Обов’язкове | Nullable | Правила |
|---|---|---:|---:|---|
| `code` | `ApiErrorCode` | так | ні | Стабільний машинний код із дозволеного переліку. |
| `message` | string | так | ні | Непорожнє пояснення для клієнта; не містить внутрішніх stack trace або SQL. |
| `field` | string | умовно | ні | Обов’язкове для помилки конкретного path/query/header/body поля; шлях поля, наприклад `amount`, `date_range`, `X-Client-Local-Date`. |
| `rule` | string | умовно | ні | Обов’язкове разом із `field`; стабільна назва порушеного правила. |

`field` і `rule` або присутні разом, або обидва відсутні. Невідомі поля заборонені.

### 7.2 `ErrorResponse`

| Поле | Тип | Обов’язкове | Nullable | Правила |
|---|---|---:|---:|---|
| `error` | `ErrorDetail` | так | ні | Єдиний кореневий ключ response body. |

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Поле amount повинно містити додатну суму UAH із двома десятковими знаками.",
    "field": "amount",
    "rule": "positive_decimal_with_two_fraction_digits"
  }
}
```

### 7.3 `ApiErrorCode`

| Код помилки | HTTP | Застосування |
|---|---:|---|
| `MALFORMED_JSON` | 400 | Request body не є синтаксично коректним JSON. |
| `RESOURCE_NOT_FOUND` | 404 | Category або Transaction за потрібним ID не існує. |
| `METHOD_NOT_ALLOWED` | 405 | URI існує, але метод не входить до погоджених операцій. |
| `CATEGORY_NAME_CONFLICT` | 409 | Нормалізована Category Name дублює іншу назву в межах типу. |
| `CATEGORY_IN_USE` | 409 | Видалення Category заборонене через пов’язану Transaction. |
| `UNSUPPORTED_MEDIA_TYPE` | 415 | Медіатип не `application/json` або параметри медіатипу некоректні. |
| `VALIDATION_ERROR` | 422 | Порушено тип, формат, обов’язковість, дозволене значення або доменне правило поля/параметра. |
| `DATA_READ_ERROR` | 500 | Збережені дані неможливо прочитати; вони не змінюються. |
| `DATA_WRITE_ERROR` | 500 | Результат зміни неможливо стійко й атомарно зберегти. |
| `INTERNAL_ERROR` | 500 | Інша неочікувана внутрішня помилка без розкриття технічних деталей. |

### 7.4 Приклади основних негативних сценаріїв

Некоректний Date Range (`422`):

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Початкова дата Date Range не може бути пізнішою за кінцеву.",
    "field": "date_range",
    "rule": "date_from_not_after_date_to"
  }
}
```

Дата Transaction пізніша за дату пристрою User (`422`):

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Дата Transaction не може бути пізнішою за поточну локальну дату пристрою User.",
    "field": "date",
    "rule": "not_after_client_local_date"
  }
}
```

Невідповідний тип Category (`422`):

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Тип Category повинен відповідати типу Transaction.",
    "field": "category_id",
    "rule": "category_type_matches_transaction_type"
  }
}
```

Дублікат Category Name (`409`):

```json
{
  "error": {
    "code": "CATEGORY_NAME_CONFLICT",
    "message": "Category з такою назвою вже існує в межах цього типу.",
    "field": "name",
    "rule": "unique_case_insensitive_within_type"
  }
}
```

Використана Category (`409`):

```json
{
  "error": {
    "code": "CATEGORY_IN_USE",
    "message": "Category не можна видалити, оскільки її використовує Transaction."
  }
}
```

Ресурс не знайдено (`404`):

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Transaction з указаним ID не існує.",
    "field": "transaction_id",
    "rule": "resource_exists"
  }
}
```

Непідтримуваний медіатип (`415`):

```json
{
  "error": {
    "code": "UNSUPPORTED_MEDIA_TYPE",
    "message": "Request body повинен використовувати медіатип application/json.",
    "field": "Content-Type",
    "rule": "application_json_media_type"
  }
}
```

Нечитабельні збережені дані (`500`):

```json
{
  "error": {
    "code": "DATA_READ_ERROR",
    "message": "Збережені дані неможливо прочитати. Дані не було змінено."
  }
}
```

## 8. Зв’язок схем з операціями

REQ-ID для всіх дев’яти операцій уже точно зафіксовані в `docs/api-operation-contracts.md`; тут вони не дублюються. Перевірено, що схема кожної операції відповідає її наявному зв’язку з вимогами.

| Operation | Request schema | Success response schema | Error schema |
|---|---|---|---|
| `POST /api/categories` | `CategoryCreate` | `CategoryCreateResponse` (`Category`) | `ErrorResponse` |
| `GET /api/categories` | немає | `CategoryListResponse` | `ErrorResponse` |
| `PATCH /api/categories/{category_id}` | `CategoryPatch` | `CategoryPatchResponse` (`Category`) | `ErrorResponse` |
| `DELETE /api/categories/{category_id}` | немає | `204 No Content` | `ErrorResponse` |
| `POST /api/transactions` | `TransactionCreate` | `TransactionCreateResponse` (`Transaction`) | `ErrorResponse` |
| `GET /api/transactions` | `TransactionFilterQuery` | `TransactionListResponse` | `ErrorResponse` |
| `PATCH /api/transactions/{transaction_id}` | `TransactionPatch` | `TransactionPatchResponse` (`Transaction`) | `ErrorResponse` |
| `DELETE /api/transactions/{transaction_id}` | немає | `204 No Content` | `ErrorResponse` |
| `GET /api/financial-summary` | немає | `FinancialSummaryResponse` | `ErrorResponse` |

## 9. Перевірка узгодженості

- Усі дев’ять операцій мають request/response/error schemas відповідно до їх контрактів.
- Усі `REQ-F-001`–`REQ-F-024` залишаються покритими через зв’язки в `docs/api-operation-contracts.md`; `REQ-NF-001`–`REQ-NF-006` відображені в атомарності, persistence, безпеці тексту, помилках і термінології.
- Category підтримує лише створення, список, перейменування й дозволене видалення.
- Transaction підтримує лише створення, список/Filter, часткове редагування й остаточне видалення.
- Financial Summary не приймає Filter і охоплює всі Transaction.
- Нових ресурсів, користувацьких можливостей, OpenAPI-опису або реалізації не додано.
