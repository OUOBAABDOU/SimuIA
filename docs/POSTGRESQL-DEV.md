# PostgreSQL local development

## Prerequisites

- Docker Engine + Docker Compose
- Python 3.11+ for local backend development

## Start PostgreSQL and FastAPI

From the repository root:

```bash
docker compose up --build
```

The Compose stack:

1. starts PostgreSQL 17;
2. waits for the PostgreSQL healthcheck;
3. builds the FastAPI image;
4. runs `alembic upgrade head`;
5. starts FastAPI on `http://localhost:8000`.

## Verify

```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/health/db
```

The second endpoint proves that FastAPI can execute a query against PostgreSQL.

## Run database integration tests

The database must already be running and migrated.

```bash
cd backend
RUN_DB_TESTS=1 pytest
```

The integration test creates a candidate, CV and job offer, reads them back, then deletes the user and verifies the cascade.

## Reset the database

For a clean development database:

```bash
docker compose down -v
docker compose up --build
```

> `down -v` deletes the PostgreSQL volume and therefore all local development data.

## Migration policy

Schema changes must be made through Alembic migrations. Do not use `Base.metadata.create_all()` in application startup.

The project uses SQLAlchemy 2.x async for runtime access and the synchronous PostgreSQL driver through Alembic, which is a supported Alembic pattern. See the official Alembic asyncio cookbook.
