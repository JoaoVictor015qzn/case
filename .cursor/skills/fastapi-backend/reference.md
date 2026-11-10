# Referência oficial: FastAPI

Fontes:
- Skill oficial do FastAPI, que vem dentro do pacote (`fastapi/.agents/skills/fastapi/`) e pode ser instalada com `uvx library-skills`
- https://fastapi.tiangolo.com/advanced/settings/
- https://fastapi.tiangolo.com/advanced/events/
- https://github.com/fastapi/full-stack-fastapi-template (backend/)

## Annotated + alias de dependência (skill oficial)

```python
from typing import Annotated
from fastapi import Depends, FastAPI

app = FastAPI()

def get_current_user():
    return {"username": "johndoe"}

CurrentUserDep = Annotated[dict, Depends(get_current_user)]

@app.get("/items/")
async def read_item(current_user: CurrentUserDep):
    return {"message": "Hello World"}
```

## Dependência com `yield` (sessão de banco)

```python
def get_db():
    db = DBSession()
    try:
        yield db
    finally:
        db.close()

DBDep = Annotated[DBSession, Depends(get_db)]
```

O padrão do template oficial com SQLModel:

```python
def get_db() -> Generator[Session]:
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_db)]
```

"Avoid creating class dependencies when possible. [...] instead create a regular function dependency that returns a class instance."

## Return type (skill oficial)

```python
@app.get("/items/me")
async def get_item() -> Item:
    return Item(name="Plumbus", description="All-purpose home device")
```

"Return types or response models filter data to avoid exposing sensitive information, and they let Pydantic serialize the data on the Rust side for performance."

## Router (skill oficial)

```python
router = APIRouter(prefix="/items", tags=["items"])

@router.get("/")
async def list_items():
    return []

app.include_router(router)
```

## Async vs sync (skill oficial)

"Use `async` *path operations* only when fully certain that the logic called inside is compatible with async and await, and that it doesn't block. [...] In case of doubt, or by default, use regular `def` functions."

Para misturar os dois, a skill oficial recomenda o Asyncer:

```python
from asyncer import asyncify

@app.get("/items/")
async def read_items():
    result = await asyncify(do_blocking_work)(name="World")
    return {"message": result}
```

## Settings (advanced/settings)

```python
from functools import lru_cache
from typing import Annotated
from fastapi import Depends, FastAPI
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Awesome API"
    admin_email: str
    model_config = SettingsConfigDict(env_file=".env")

@lru_cache
def get_settings():
    return Settings()

@app.get("/info")
async def info(settings: Annotated[Settings, Depends(get_settings)]):
    return {"app_name": settings.app_name}
```

Override nos testes:

```python
def get_settings_override():
    return Settings(admin_email="testing_admin@example.com")

app.dependency_overrides[get_settings] = get_settings_override
```

Template oficial: `SettingsConfigDict(env_file="../.env", env_ignore_empty=True, extra="ignore")` e um validator que troca `postgresql://` por `postgresql+psycopg://`:

```python
@field_validator("DATABASE_URL", mode="before")
@classmethod
def _use_psycopg_driver(cls, value: str | PostgresDsn) -> str:
    database_url = str(value)
    for scheme in ("postgres://", "postgresql://"):
        if database_url.startswith(scheme):
            return database_url.replace(scheme, "postgresql+psycopg://", 1)
    return database_url
```

## Lifespan (advanced/events)

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    ml_models["answer_to_everything"] = fake_answer_to_everything_ml_model
    yield
    ml_models.clear()

app = FastAPI(lifespan=lifespan)
```

"If you provide a `lifespan` parameter, `startup` and `shutdown` event handlers will no longer be called."

## Exception handlers (tutorial/handling-errors)

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

class UnicornException(Exception):
    def __init__(self, name: str):
        self.name = name

app = FastAPI()

@app.exception_handler(UnicornException)
async def unicorn_exception_handler(request: Request, exc: UnicornException):
    return JSONResponse(
        status_code=418,
        content={"message": f"Oops! {exc.name} did something. There goes a rainbow..."},
    )
```

## Ferramentas (skill oficial: other-tools)

- **uv** para dependências, **Ruff** para lint e formatação, **ty** para checagem de tipos.
- **HTTPX** para HTTP, preferido a Requests. **SQLModel** para SQL, preferido ao SQLAlchemy puro. **Asyncer** para misturar sync e async.

## Ruff do template oficial (pyproject.toml)

```toml
[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP", "ARG001", "T201"]
ignore = ["E501", "B008", "W191", "B904"]
```
