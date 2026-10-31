# Контракти операцій REST API Personal Finance System

**Статус:** DESIGN FOR MOCK API
**Дата:** 2026-10-31
**Базова адреса:** `http://localhost:<port>/api`
**Джерела:** `spec/srs.md`, `spec/bdd-scenarios.md`, `spec/glossary.md`, `spec/addendum.md`, `docs/api-resource-model.md`

## 1. Загальні правила

- Запити й відповіді з тілом використовують медіатип `application/json`. Допускаються коректні параметри медіатипу, наприклад `application/json; charset=utf-8`; порівняння не є буквальним порівнянням усього рядка заголовка.
- `Category ID` і `Transaction ID` у контракті представлені додатними цілими числами.
- `type` приймає лише рядок `income` або `expense`.
- `amount`, `total_income`, `total_expenses` і `current_balance` передаються як десяткові рядки UAH із рівно двома цифрами після крапки, наприклад `"1250.00"`. `amount` має бути більшим за `0.00`.
- Дати передаються рядками формату `YYYY-MM-DD` і мають бути реальними календарними датами.
- Невідомі поля JSON відхиляються з `422 Unprocessable Content`, щоб помилки контракту не приховувалися.
- Усі операції зміни є атомарними. Успішний статус повертається лише після стійкого збереження повного результату; помилка не залишає часткових змін (`REQ-F-001`, `REQ-NF-001`, `REQ-NF-002`).
- Текстові значення обробляються лише як дані (`REQ-NF-004`).
- Помилки збережених даних не змінюють їх і повертаються як `500 Internal Server Error`; Flet-клієнт повідомляє User (`REQ-NF-003`).
- Автентифікація не використовується, оскільки SRS визначає одного локального User і не передбачає облікових записів.

### 1.1 Формат помилки

Усі помилкові відповіді мають JSON-тіло:

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

`code` і `message` обов’язкові. `field` і `rule` обов’язкові для помилок введення та валідації, щоб клієнт виконав `REQ-NF-005`; для загальних помилок вони можуть бути відсутні.

### 1.2 Спільні HTTP-коди

| Код | Значення |
|---|---|
| `400 Bad Request` | Тіло не є синтаксично коректним JSON. Застосовується лише до операцій із request body. |
| `405 Method Not Allowed` | Для URI використано HTTP-метод, якого немає серед дев’яти визначених операцій. |
| `415 Unsupported Media Type` | Операція з request body отримала медіатип, відмінний від `application/json`, або некоректні параметри медіатипу. Коректні параметри, зокрема `charset=utf-8`, дозволені. |
| `422 Unprocessable Content` | Параметр або JSON синтаксично прочитано, але він відсутній, має неправильний тип, формат, значення чи порушує правило валідації. |
| `500 Internal Server Error` | Сервер не може прочитати або стійко зберегти дані чи завершити операцію без порушення цілісності. Дані не змінюються частково. |

## 2. POST `/api/categories`

**Призначення:** створити Category.
**REQ-ID:** `REQ-F-010`, `REQ-F-011`; наскрізно `REQ-F-001`, `REQ-NF-001`, `REQ-NF-002`, `REQ-NF-004`, `REQ-NF-005`.

### Parameters

| Розташування | Назва | Тип | Обов’язковість | Обмеження |
|---|---|---|---|---|
| Header | `Content-Type` | string | так | Медіатип `application/json`; дозволені коректні параметри, наприклад `charset=utf-8`. |

Path і query parameters відсутні. Спеціальні заголовки, крім `Content-Type`, не потрібні.

### Request body

| Поле | Тип | Обов’язковість | Правила |
|---|---|---|---|
| `name` | string | так | Після видалення початкових і кінцевих пробілів: не порожнє, не більше 50 символів, унікальне без урахування регістру в межах `type`. Зберігається без крайніх пробілів. |
| `type` | string | так | `income` або `expense`. |

```json
{
  "name": "Зарплата",
  "type": "income"
}
```

### Successful response

`201 Created` повертає створену Category з присвоєним Category ID.

```json
{
  "id": 1,
  "name": "Зарплата",
  "type": "income"
}
```

### Status codes

| Код | Коли повертається |
|---|---|
| `201 Created` | Category успішно перевірена і стійко збережена з новим Category ID. |
| `400 Bad Request` | Некоректний JSON. |
| `415 Unsupported Media Type` | Медіатип не є `application/json` або його параметри некоректні. |
| `409 Conflict` | Category з такою самою нормалізованою назвою вже існує в межах цього типу. |
| `422 Unprocessable Content` | Відсутні `name`/`type`, неправильний тип значення, недопустимий `type`, порожня або задовга назва чи невідоме поле. |
| `500 Internal Server Error` | Дані неможливо прочитати або Category неможливо стійко зберегти. |

## 3. GET `/api/categories`

**Призначення:** отримати список усіх Category.
**REQ-ID:** `REQ-F-012`; наскрізно `REQ-NF-003`, `REQ-NF-006`.

### Parameters

Path, query і спеціальні header parameters відсутні.

### Request body

Відсутнє.

### Successful response

`200 OK` повертає JSON-масив. За відсутності Category повертається `[]`.

```json
[
  {
    "id": 1,
    "name": "Зарплата",
    "type": "income"
  },
  {
    "id": 2,
    "name": "Їжа",
    "type": "expense"
  }
]
```

### Status codes

| Код | Коли повертається |
|---|---|
| `200 OK` | Список успішно отримано, включно з порожнім списком. |
| `500 Internal Server Error` | Збережені Category неможливо прочитати. |

## 4. PATCH `/api/categories/{category_id}`

**Призначення:** частково оновити Category лише шляхом перейменування.
**REQ-ID:** `REQ-F-011`, `REQ-F-013`; наскрізно `REQ-F-001`, `REQ-NF-001`, `REQ-NF-002`, `REQ-NF-004`, `REQ-NF-005`.

### Parameters

| Розташування | Назва | Тип | Обов’язковість | Обмеження |
|---|---|---|---|---|
| Path | `category_id` | integer | так | Додатне ціле число; незмінний Category ID. |
| Header | `Content-Type` | string | так | Медіатип `application/json`; дозволені коректні параметри, наприклад `charset=utf-8`. |

Query parameters відсутні.

### Request body

| Поле | Тип | Обов’язковість | Правила |
|---|---|---|---|
| `name` | string | так | Єдине дозволене поле. Після trim: не порожнє, до 50 символів, унікальне без урахування регістру в межах незмінного типу Category. |

PATCH є частковим: `id` і `type` не передаються та не змінюються. Порожній об’єкт, `name: null` або будь-яке інше поле відхиляються.

```json
{
  "name": "Харчування"
}
```

### Successful response

`200 OK` повертає повне актуальне представлення Category.

```json
{
  "id": 2,
  "name": "Харчування",
  "type": "expense"
}
```

### Status codes

| Код | Коли повертається |
|---|---|
| `200 OK` | Category перейменовано без зміни Category ID або типу. |
| `400 Bad Request` | Некоректний JSON. |
| `404 Not Found` | Category з указаним `category_id` не існує. |
| `409 Conflict` | Нова нормалізована назва дублює іншу Category того самого типу. |
| `415 Unsupported Media Type` | Медіатип не є `application/json` або його параметри некоректні. |
| `422 Unprocessable Content` | Некоректний ID, відсутнє/некоректне `name`, порожній об’єкт або заборонене поле. |
| `500 Internal Server Error` | Дані неможливо прочитати або перейменування неможливо стійко зберегти. |

## 5. DELETE `/api/categories/{category_id}`

**Призначення:** видалити Category, яку не використовує жодна Transaction.
**REQ-ID:** `REQ-F-014`; наскрізно `REQ-F-001`, `REQ-NF-001`, `REQ-NF-002`.

### Parameters

| Розташування | Назва | Тип | Обов’язковість | Обмеження |
|---|---|---|---|---|
| Path | `category_id` | integer | так | Додатне ціле число; Category ID. |

Query і спеціальні header parameters відсутні.

### Request body

Відсутнє.

### Successful response

`204 No Content`. Тіло відповіді відсутнє. Повторний DELETE того самого ID повертає `404 Not Found`, а не повторний успіх.

### Status codes

| Код | Коли повертається |
|---|---|
| `204 No Content` | Невикористану Category остаточно видалено; response body відсутнє. |
| `404 Not Found` | Category з указаним ID не існує. |
| `409 Conflict` | Category використовується хоча б однією Transaction; Category і Transaction залишаються без змін. |
| `422 Unprocessable Content` | `category_id` не є додатним цілим числом. |
| `500 Internal Server Error` | Залежності неможливо перевірити або видалення неможливо стійко завершити. |

## 6. POST `/api/transactions`

**Призначення:** створити Transaction.
**REQ-ID:** `REQ-F-002`, `REQ-F-003`, `REQ-F-004`, `REQ-F-005`, `REQ-F-006`, `REQ-F-007`; наскрізно `REQ-F-001`, `REQ-NF-001`, `REQ-NF-002`, `REQ-NF-004`, `REQ-NF-005`.

### Parameters

| Розташування | Назва | Тип | Обов’язковість | Обмеження |
|---|---|---|---|---|
| Header | `Content-Type` | string | так | Медіатип `application/json`; дозволені коректні параметри, наприклад `charset=utf-8`. |
| Header | `X-Client-Local-Date` | string | так | Реальна дата формату `YYYY-MM-DD`; поточна локальна дата пристрою User для перевірки `date`. |

Path і query parameters відсутні.

### Request body

| Поле | Тип | Обов’язковість | Правила |
|---|---|---|---|
| `type` | string | так | `income` або `expense`. |
| `amount` | string | так | Додатний десятковий рядок UAH із рівно двома цифрами після крапки. |
| `date` | string | так | Реальна дата `YYYY-MM-DD`, не пізніша за `X-Client-Local-Date`. |
| `category_id` | integer | так | Додатний ID наявної Category, `type` якої збігається з Transaction `type`. |
| `description` | string або null | ні | Відсутнє або `null` означає відсутність Description; рядок має не більше 255 символів. |

```json
{
  "type": "income",
  "amount": "25000.00",
  "date": "2026-10-30",
  "category_id": 1,
  "description": null
}
```

### Successful response

`201 Created` повертає створену Transaction з присвоєним Transaction ID.

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

### Status codes

| Код | Коли повертається |
|---|---|
| `201 Created` | Transaction пройшла всі перевірки й стійко збережена з новим Transaction ID. |
| `400 Bad Request` | Некоректний JSON. |
| `404 Not Found` | Category з указаним `category_id` не існує. |
| `415 Unsupported Media Type` | Медіатип не є `application/json` або його параметри некоректні. |
| `422 Unprocessable Content` | Відсутній/некоректний заголовок, поле чи тип; сума недодатна або неканонічна; дата неіснуюча/майбутня; Description задовгий; тип Category не відповідає Transaction; є невідоме поле. |
| `500 Internal Server Error` | Дані неможливо прочитати або Transaction неможливо стійко зберегти. |

## 7. GET `/api/transactions`

**Призначення:** отримати Transaction List без Filter або з Filter.
**REQ-ID:** `REQ-F-002`, `REQ-F-015`, `REQ-F-016`, `REQ-F-017`, `REQ-F-018`, `REQ-F-019`, `REQ-F-020`; наскрізно `REQ-NF-003`, `REQ-NF-006`.

### Parameters

| Розташування | Назва | Тип | Обов’язковість | Обмеження |
|---|---|---|---|---|
| Query | `type` | string | ні | `income` або `expense`. |
| Query | `category_id` | integer | ні | Додатне ціле число. Неіснуючий, але коректний ID дає порожній результат. |
| Query | `date_from` | string | ні | Реальна дата `YYYY-MM-DD`; передається тільки разом із `date_to`; межа включна. |
| Query | `date_to` | string | ні | Реальна дата `YYYY-MM-DD`; передається тільки разом із `date_from`; межа включна; не раніше `date_from`. |

Path і спеціальні header parameters відсутні. Кілька активних Filter поєднуються через AND.

### Request body

Відсутнє.

### Successful response

`200 OK` повертає масив Transaction, упорядкований за `date` від новіших до старіших. Порядок однакових дат не гарантується. API передає `id`, але Flet-клієнт не показує його у Transaction List.

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
  },
  {
    "id": 11,
    "type": "expense",
    "amount": "850.50",
    "date": "2026-10-29",
    "category_id": 2,
    "category_name": "Їжа",
    "description": "Продукти"
  }
]
```

За відсутності збережених Transaction або збігів Filter успішна відповідь є `[]`. Клієнт визначає потрібне інформаційне повідомлення за наявністю активних Filter.

### Status codes

| Код | Коли повертається |
|---|---|
| `200 OK` | Список успішно отримано, включно з порожнім результатом. |
| `422 Unprocessable Content` | Некоректний query parameter, задана лише одна межа Date Range або `date_from` пізніша за `date_to`. Filter не застосовується. |
| `500 Internal Server Error` | Збережені Transaction або пов’язані Category неможливо прочитати. |

## 8. PATCH `/api/transactions/{transaction_id}`

**Призначення:** частково оновити Transaction зі збереженням Transaction ID.
**REQ-ID:** `REQ-F-002`, `REQ-F-004`, `REQ-F-005`, `REQ-F-006`, `REQ-F-007`, `REQ-F-008`; наскрізно `REQ-F-001`, `REQ-NF-001`, `REQ-NF-002`, `REQ-NF-004`, `REQ-NF-005`.

### Parameters

| Розташування | Назва | Тип | Обов’язковість | Обмеження |
|---|---|---|---|---|
| Path | `transaction_id` | integer | так | Додатне ціле число; незмінний Transaction ID. |
| Header | `Content-Type` | string | так | Медіатип `application/json`; дозволені коректні параметри, наприклад `charset=utf-8`. |
| Header | `X-Client-Local-Date` | string | так | Реальна дата `YYYY-MM-DD`; поточна локальна дата пристрою User. |

Query parameters відсутні.

### Request body

Усі поля необов’язкові окремо, але тіло повинно містити принаймні одне дозволене поле. Пропущене поле не змінюється. Явне `null` дозволене лише для `description` і видаляє Description.

| Поле | Тип | Обов’язковість | Правила |
|---|---|---|---|
| `type` | string | ні | `income` або `expense`. |
| `amount` | string | ні | Додатний десятковий рядок UAH із двома цифрами після крапки. |
| `date` | string | ні | Реальна дата `YYYY-MM-DD`, не пізніша за `X-Client-Local-Date`. |
| `category_id` | integer | ні | Додатний ID наявної Category. |
| `description` | string або null | ні | Рядок до 255 символів; `null` прибирає Description. |

Після накладання переданих полів сервер перевіряє весь результуючий стан за правилами створення. Якщо змінено `type`, наявна або одночасно передана Category повинна мати новий відповідний тип. `id` і `category_name` передавати заборонено.

```json
{
  "amount": "27500.00",
  "description": "Зарплата з премією"
}
```

### Successful response

`200 OK` повертає повне оновлене представлення Transaction.

```json
{
  "id": 10,
  "type": "income",
  "amount": "27500.00",
  "date": "2026-10-30",
  "category_id": 1,
  "category_name": "Зарплата",
  "description": "Зарплата з премією"
}
```

### Status codes

| Код | Коли повертається |
|---|---|
| `200 OK` | Передані поля застосовано атомарно; Transaction ID не змінився. |
| `400 Bad Request` | Некоректний JSON. |
| `404 Not Found` | Transaction або передана Category не існує. |
| `415 Unsupported Media Type` | Медіатип не є `application/json` або його параметри некоректні. |
| `422 Unprocessable Content` | Некоректний ID/header/поле; порожній об’єкт; заборонене поле; `null` не для Description; результуючий стан порушує правила Transaction або відповідність типу Category. Попередній стан збережено. |
| `500 Internal Server Error` | Дані неможливо прочитати або оновлення неможливо стійко зберегти. |

## 9. DELETE `/api/transactions/{transaction_id}`

**Призначення:** остаточно видалити Transaction.
**REQ-ID:** `REQ-F-009`; наскрізно `REQ-F-001`, `REQ-NF-001`, `REQ-NF-002`.

### Parameters

| Розташування | Назва | Тип | Обов’язковість | Обмеження |
|---|---|---|---|---|
| Path | `transaction_id` | integer | так | Додатне ціле число; Transaction ID. |

Query і спеціальні header parameters відсутні.

### Request body

Відсутнє.

### Successful response

`204 No Content`. Тіло відповіді відсутнє. Після видалення Transaction більше не входить до Transaction List і фінансових показників. Повторний DELETE повертає `404 Not Found`.

### Status codes

| Код | Коли повертається |
|---|---|
| `204 No Content` | Transaction остаточно видалено; response body відсутнє. |
| `404 Not Found` | Transaction з указаним ID не існує. |
| `422 Unprocessable Content` | `transaction_id` не є додатним цілим числом. |
| `500 Internal Server Error` | Дані неможливо прочитати або видалення неможливо стійко завершити. |

## 10. GET `/api/financial-summary`

**Призначення:** отримати Total Income, Total Expenses і Current Balance за всіма збереженими Transaction.
**REQ-ID:** `REQ-F-002`, `REQ-F-021`, `REQ-F-022`, `REQ-F-023`, `REQ-F-024`; наскрізно `REQ-NF-003`, `REQ-NF-006`.

### Parameters

Path, query і спеціальні header parameters відсутні. Операція навмисно не приймає Filter.

### Request body

Відсутнє.

### Successful response

`200 OK` повертає три показники за всіма Transaction. За відсутності Transaction всі значення дорівнюють `"0.00"`. Current Balance може бути від’ємним.

```json
{
  "total_income": "25000.00",
  "total_expenses": "850.50",
  "current_balance": "24149.50"
}
```

### Status codes

| Код | Коли повертається |
|---|---|
| `200 OK` | Показники успішно обчислено за всіма збереженими Transaction, незалежно від Filter клієнта. |
| `500 Internal Server Error` | Transaction неможливо прочитати або показники неможливо коректно обчислити. |

## 11. Перевірка повноти

| № | Operation | Основні REQ-ID |
|---:|---|---|
| 1 | `POST /api/categories` | `REQ-F-010`, `REQ-F-011` |
| 2 | `GET /api/categories` | `REQ-F-012` |
| 3 | `PATCH /api/categories/{category_id}` | `REQ-F-011`, `REQ-F-013` |
| 4 | `DELETE /api/categories/{category_id}` | `REQ-F-014` |
| 5 | `POST /api/transactions` | `REQ-F-002`–`REQ-F-007` |
| 6 | `GET /api/transactions` | `REQ-F-002`, `REQ-F-015`–`REQ-F-020` |
| 7 | `PATCH /api/transactions/{transaction_id}` | `REQ-F-002`, `REQ-F-004`–`REQ-F-008` |
| 8 | `DELETE /api/transactions/{transaction_id}` | `REQ-F-009` |
| 9 | `GET /api/financial-summary` | `REQ-F-002`, `REQ-F-021`–`REQ-F-024` |

`REQ-F-001` є наскрізною вимогою persistence для всіх успішних операцій зміни. `REQ-NF-001`–`REQ-NF-006` застосовано як правила стійкості, атомарності, безпечної обробки тексту, помилок і термінології. Усі дев’ять операцій із `docs/api-resource-model.md` деталізовано без додавання нових користувацьких можливостей.
