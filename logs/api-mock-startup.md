# Запуск Prism mock API

**Дата перевірки:** 2026-10-31
**OpenAPI specification:** `spec/openapi.json`
**Результат:** PASS

## 1. Версії та сумісність

- Node.js: `v24.11.1`
- npm: `11.6.2`
- актуальний Prism CLI на час перевірки: `5.16.0`
- вимога Prism CLI `5.16.0`: Node.js `>=24.18.0`
- використана сумісна версія Prism CLI: `5.14.2`
- вимога Prism CLI `5.14.2`: Node.js `>=18.20.1`

Node.js `v24.11.1` не відповідає вимозі найновішого Prism `5.16.0`, але повністю сумісний із зафіксованим офіційним Prism `5.14.2`. Оновлення Node.js для цього запуску не потрібне. Глобальне встановлення Prism не виконувалося.

Під час завантаження `npx` показав deprecation warnings для транзитивних залежностей `uuid@8.3.2`, `json-schema-ref-parser@6.1.0` і `@faker-js/faker@5.5.3`. Вони належать пакету Prism 5.14.2, не блокують запуск і не змінюють проєкт.

## 2. Фактично виконані команди

Перевірка версій і `engines`:

```powershell
node --version
npm --version
npm view @stoplight/prism-cli version engines --json
npm view @stoplight/prism-cli@5.14.2 version engines --json
```

Запуск mock API:

```powershell
npx --yes @stoplight/prism-cli@5.14.2 mock spec/openapi.json -p 4010
```

Тестові запити:

```powershell
curl.exe -sS -i http://127.0.0.1:4010/categories
curl.exe -sS -i http://127.0.0.1:4010/api/categories
```

## 3. Зареєстровані маршрути

Prism повідомив про завантаження всіх 9 operations:

1. `POST http://127.0.0.1:4010/categories`
2. `GET http://127.0.0.1:4010/categories`
3. `PATCH http://127.0.0.1:4010/categories/{category_id}`
4. `DELETE http://127.0.0.1:4010/categories/{category_id}`
5. `POST http://127.0.0.1:4010/transactions`
6. `GET http://127.0.0.1:4010/transactions`
7. `PATCH http://127.0.0.1:4010/transactions/{transaction_id}`
8. `DELETE http://127.0.0.1:4010/transactions/{transaction_id}`
9. `GET http://127.0.0.1:4010/financial-summary`

Для path parameters Prism показав згенеровані прикладні числові значення, що відповідають схемі `PositiveId`.

## 4. Адреса й особливість `/api`

Prism слухав на:

```text
http://127.0.0.1:4010
```

Хоча OpenAPI `servers[0].url` містить `/api`, Prism CLI 5.14.2 зареєстрував маршрути без цього server base prefix, безпосередньо за значеннями `paths`. Тому для цього mock використовуються `/categories`, `/transactions` і `/financial-summary`.

Контракт не змінювався заради поведінки Prism. Перевірочний `GET /api/categories` повернув `404 Not Found` із Prism-помилкою `NO_PATH_MATCHED_ERROR`, що підтверджує фактичний routing.

## 5. Результат простого GET-запиту

Запит:

```http
GET http://127.0.0.1:4010/categories
```

Фактичний статус:

```text
HTTP/1.1 200 OK
Content-Type: application/json
```

Фактичне JSON-тіло:

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

Prism додатково зафіксував, що запит пройшов validation rules і відповідь обрано зі статусом `200`.

## 6. Повторний запуск і зупинка у Windows PowerShell

Рекомендований інтерактивний запуск із кореня репозиторію:

```powershell
npx --yes @stoplight/prism-cli@5.14.2 mock spec/openapi.json -p 4010
```

Адреса перевірки після запуску:

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:4010/categories
```

Зупинка інтерактивного процесу:

```text
Ctrl+C
```

За потреби прихованого фонового запуску:

```powershell
$prismProcess = Start-Process -FilePath "npx.cmd" -ArgumentList @("--yes", "@stoplight/prism-cli@5.14.2", "mock", "spec/openapi.json", "-p", "4010") -PassThru -WindowStyle Hidden
```

Зупинка створеного фонового process tree:

```powershell
taskkill.exe /PID $prismProcess.Id /T /F
```

## 7. Висновок

Prism mock API успішно запущено зі специфікації, усі 9 operations завантажено, HTTP-запит прийнято й повернуто валідну JSON-відповідь. FastAPI, SQLite, Flet-клієнт, бізнес-логіку або іншу серверну реалізацію не створено.
