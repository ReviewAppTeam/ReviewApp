# ReviewApp

## Структура

```
apps/
  web/        React + TypeScript, Vite
  backend/    Python 3.14, FastAPI, Postgres
```

## Що потрібно

- Node 26 через [nvm](https://github.com/nvm-sh/nvm)
- pnpm 12: `npm install -g pnpm@12`
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Docker

## Сетап

```bash
nvm install
pnpm install
cd apps/backend && uv sync && cp .env.example .env && cd ../..
docker compose up -d postgres
pnpm --filter @reviewapp/backend migrate
```

Postgres слухає порт 5432. Якщо він зайнятий, необхідно створити в корені `.env` з `POSTGRES_PORT=5433` і поставити той самий порт у `DATABASE_URL` в `apps/backend/.env`.

## Запуск

Спочатку `nvm use`, потім у двох терміналах:

```bash
pnpm backend
```

```bash
pnpm web
```

Фронт: http://localhost:5173. Swagger: http://localhost:8000/docs.

## Імпорт відгуків

`POST /api/v1/reviews/import` приймає CSV (UTF-8) з колонками `source,author,rating,text,date`. Приклад: `apps/backend/samples/reviews.csv`.

```bash
curl -F "file=@apps/backend/samples/reviews.csv" http://localhost:8000/api/v1/reviews/import
```

Повторний імпорт тих самих відгуків їх не дублює. Список: `GET /api/v1/reviews?page=1&page_size=20`, найновіші зверху.

## Команди

| Команда                                             | Що робить                                                  |
| --------------------------------------------------- | ---------------------------------------------------------- |
| `pnpm lint`                                         | лінтери                                                    |
| `pnpm typecheck`                                    | перевірка типів                                            |
| `pnpm test`                                         | тести                                                      |
| `pnpm format`                                       | форматування                                               |
| `pnpm api:sync`                                     | оновити `openapi.json` і API-клієнт після зміни ендпоінтів |
| `pnpm --filter @reviewapp/backend migration "опис"` | нова міграція                                              |
| `pnpm --filter @reviewapp/backend migrate`          | застосувати міграції                                       |

## Git

- Фічі робимо в гілках на кшталт `feat/csv-import` і через PR зливаємо в `dev`.
- `dev` деплоїться на dev, `main` на prod. У `main` потрапляє тільки через PR `dev → main`.
- Прямий пуш у `dev` і `main` заборонений.
- Коміти у форматі `type(scope): опис`, наприклад `feat(backend): import reviews from CSV`.
- Типи: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.
- Scope (необов'язково): `web`, `backend`, `ci`, `docker`, `deps`, `repo`, `release`.
- Формат перевіряє хук при коміті і CI у кожному PR.
