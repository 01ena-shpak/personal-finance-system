# Валідація OpenAPI specification

**Дата:** 2026-10-31
**Файл:** `spec/openapi.json`
**Підсумковий статус:** PASS

## 1. Середовище

- Node.js: `v24.11.1`
- npm: `11.6.2`
- Redocly CLI: `2.72.1`
- Спосіб запуску: офіційний npm-пакет `@redocly/cli` через `npx`, без глобального встановлення.

## 2. Фактично виконані команди

```powershell
node --version
npm --version
npx --yes @redocly/cli@latest --version
npx --yes @redocly/cli@latest lint spec/openapi.json
npx --yes @redocly/cli@latest lint spec/openapi.json
npx --yes @redocly/cli@latest lint --help
npx --yes @redocly/cli@latest lint spec/openapi.json --extends minimal
npx --yes @redocly/cli@latest lint spec/openapi.json --format json
```

Після Redocly додатково виконано локальні read-only перевірки PowerShell: JSON parsing, підрахунок operations і schemas, унікальність `operationId`, точні набори `x-req-ids`, розв’язання локальних `$ref`, наявність request/response schemas і прикладів, path parameters, відсутність `Content-Type` як header parameter та граничні приклади грошових patterns.

## 3. Початковий Redocly recommended lint

Результат першого запуску:

- errors: 9;
- warnings: 2;
- ignored: 0;
- статус: FAIL.

Усі 9 errors створило правило `security-defined`: кожна з дев’яти operations не мала явно визначеної security-моделі. SRS навмисно визначає одного локального User і не передбачає облікових записів, авторизації чи автентифікації.

### Виправлення

До кореня `spec/openapi.json` додано:

```json
"security": []
```

Порожній масив явно означає відсутність security requirements і не додає функціональності поза SRS. Security scheme не створювалася.

## 4. Підсумкові результати Redocly

### Recommended configuration

Команда:

```powershell
npx --yes @redocly/cli@latest lint spec/openapi.json --format json
```

Результат:

- errors: 0;
- warnings: 2;
- ignored: 0;
- повідомлення Redocly: `Your API description is valid`.

### Minimal configuration — базова відповідність OpenAPI

Команда:

```powershell
npx --yes @redocly/cli@latest lint spec/openapi.json --extends minimal
```

Результат:

- errors: 0;
- warnings: 1;
- специфікацію визнано валідною.

## 5. Невиправлені warnings

### `info-license`

Recommended lint повідомляє, що `info` не містить `license`.

Попередження залишено, тому що ліцензію проєкту не визначено у затверджених документах або репозиторії. Додавання вигаданої ліцензії було б недостовірним і виходило б за межі API-контракту. Це не порушення OpenAPI 3.0.3.

### `no-server-example.com`

Recommended і minimal lint попереджають про `http://localhost:{port}/api`.

Попередження залишено, тому що `localhost` прямо затверджений в `spec/addendum.md` для локальної розробки, тестування й демонстрації на Windows 11 без зовнішнього інтернету. Заміна адреси на публічний або вигаданий host суперечила б затвердженій архітектурі. Це не порушення OpenAPI 3.0.3.

Ignore-файл або вимкнення правил не застосовувалися; обидва warnings залишаються видимими.

## 6. Додаткові структурні перевірки

Підсумок локального аудиту:

- OpenAPI version: `3.0.3`;
- operations: 9;
- component schemas: 21;
- reusable parameters: 7;
- reusable responses: 6;
- знайдено `$ref`: 105;
- нерозв’язаних `$ref`: 0;
- дубльованих `operationId`: 0;
- operations без `x-req-ids`: 0;
- розбіжностей `x-req-ids` із `docs/api-operation-contracts.md`: 0;
- пропущених `REQ-F-001`–`REQ-F-024`: 0;
- пропущених `REQ-NF-001`–`REQ-NF-006`: 0;
- проблем з обов’язковими path parameters: 0;
- `Content-Type` header parameters: 0;
- успішних JSON-відповідей без schema або позитивного прикладу: 0;
- помилкових JSON-відповідей без `ErrorResponse`: 0.

Грошові patterns додатково перевірено на граничних значеннях:

- `Amount`: `"0.00"` відхиляється, `"0.01"` і `"1250.00"` приймаються;
- `SignedMoney`: `"-0.00"` відхиляється, `"-0.50"` і `"0.00"` приймаються.

JSON успішно розібрано стандартним JSON parser. Приклади є частиною валідованого OpenAPI-документа; Redocly не виявив несумісних прикладів або схем.

## 7. Висновок

Після виправлення явного no-auth security declaration специфікація проходить Redocly CLI з 0 errors. Два recommended warnings і одне minimal warning є некритичними, не приховані та обґрунтовані вище. Підсумковий статус перевірки — **PASS**.
