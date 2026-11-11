# Referência oficial: SQLModel, Alembic e template FastAPI

Fontes:
- A skill oficial do SQLModel vem dentro do pacote (`sqlmodel/.agents/skills/sqlmodel/SKILL.md`).
- https://github.com/fastapi/full-stack-fastapi-template (`backend/app/core/db.py`, `backend/app/alembic/`, `backend/scripts/prestart.sh`)
- https://alembic.sqlalchemy.org/en/latest/cookbook.html

## Modelos (skill oficial SQLModel)

```python
class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    team_id: int | None = Field(default=None, foreign_key="team.id")
```

One-to-many com cascade:

```python
class Team(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    heroes: list["Hero"] = Relationship(back_populates="team", cascade_delete=True)

class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    team_id: int | None = Field(default=None, foreign_key="team.id", ondelete="CASCADE")
    team: Team | None = Relationship(back_populates="heroes")
```

Timestamps:

```python
from datetime import UTC, datetime

class Event(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
```

"Do not add `sa_type=DateTime(timezone=True)` [...] These overrides bypass SQLModel's UTC processing."

Escape hatch para tipos de coluna: "Use SQLModel's `Field(sa_type=...)`, `Field(sa_column=...)` [...] only when normal `Field()` parameters do not cover a column or type requirement. Do not switch the whole model to SQLAlchemy declarative style for one custom column."

## Sessão e queries

```python
with Session(engine) as session:
    heroes = session.exec(select(Hero)).all()

session.add(hero)
session.commit()
session.refresh(hero)
```

- `.all()` retorna uma lista, `.first()` um item opcional, `.one()` exige exatamente um, e `.one_or_none()` aceita zero ou um.
- Para relações, a doc diz: "prefer `Relationship(sa_relationship_kwargs={...})`". Para eager loading numa query, use `select(...).options(selectinload(Model.rel))` (de `sqlalchemy.orm`).

## Template oficial: engine e dependency

```python
# app/core/db.py
engine = create_engine(str(settings.DATABASE_URL), pool_pre_ping=True)

def init_db(session: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    # SQLModel.metadata.create_all(engine)
    ...
```

```python
# app/api/deps.py
def get_db() -> Generator[Session]:
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_db)]
```

## Template oficial: alembic `env.py` (trecho)

```python
from app.models import SQLModel  # noqa
from app.core.config import settings # noqa

target_metadata = SQLModel.metadata

def get_url():
    return str(settings.DATABASE_URL)

def run_migrations_online():
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(configuration, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()
```

`script.py.mako` do template:

```mako
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
${imports if imports else ""}
```

`alembic.ini`: `script_location = app/alembic`.

## Template oficial: `scripts/prestart.sh`

```bash
#! /usr/bin/env bash
set -e
set -x

# Run migrations
alembic upgrade head
```

## Template oficial: Postgres no compose

```yaml
db:
  image: postgres:18
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U postgres -d app"]
    interval: 10s
    retries: 5
    start_period: 30s
    timeout: 10s
  volumes:
    - app-db-data:/var/lib/postgresql
  environment:
    - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:?Variable not set}
    - POSTGRES_DB=app
```

Atenção: a partir do Postgres 18, o volume monta em `/var/lib/postgresql`, e não mais em `/var/lib/postgresql/data`.

## SQLite em testes (skill oficial)

```python
engine = create_engine("sqlite:///:memory:")
SQLModel.metadata.create_all(engine)
with Session(engine) as session:
    ...
```

Para SQLite com FastAPI: `connect_args = {"check_same_thread": False}`. Para compartilhar o banco in-memory entre threads, use também `poolclass=StaticPool`.
