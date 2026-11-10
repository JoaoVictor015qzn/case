---
name: database-sqlmodel
description: Persistência do case no Postgres com SQLModel + Alembic + psycopg 3, seguindo a skill oficial do SQLModel - tabelas requisition e requisition_item em infrastructure/persistence/tables, Decimal para dinheiro, Unit of Work e repositório em classes que mapeiam o agregado de schemas/requisition <-> tabela, idempotency key única, migrations automáticas no start e pgAdmin para inspeção. Use ao criar ou alterar tabelas, migrations, queries, o repositório ou a configuração do banco.
---

# Banco: SQLModel + Alembic + Postgres

Exemplos oficiais: [reference.md](reference.md). Regras gerais: skill `case-architecture`.

## Onde mora (uma classe por arquivo)

```
backend/app/infrastructure/persistence/
├── database.py                          # Database: engine (pool_pre_ping) + session()
├── tables/requisition_table.py          # RequisitionTable (table=True)
├── tables/requisition_item_table.py     # RequisitionItemTable (table=True)
├── mappers/requisition_table_mapper.py  # RequisitionTableMapper: agregado <-> tabelas
├── sqlmodel_requisition_repository.py   # implementa domain.ports.RequisitionRepository
├── sqlmodel_unit_of_work.py             # implementa domain.ports.UnitOfWork
└── migrations/                          # Alembic: env.py, script.py.mako, versions/
```

As tabelas são SQLModel (que também é Pydantic), mas são detalhe de persistência: ficam fora de `schemas/`. O domínio só conhece o agregado `Requisition` de `schemas/requisition/`.

## Regras da skill oficial do SQLModel

- Importe de `sqlmodel`: `Field, Relationship, Session, SQLModel, create_engine, select`.
- **Não** use `declarative_base()`, `Mapped[...]`, `mapped_column()`, `relationship()` nem `sessionmaker()`.
- Queries usam `session.exec(select(...))`, **não** `session.execute` nem `session.query`. Não adicione `.scalars()`.
- Busca por PK com `session.get(Model, id)`.
- Depois de criar: `session.add(obj)`, depois `session.commit()` e `session.refresh(obj)`.
- Datas: `datetime` aware (`datetime.now(UTC)`). O SQLModel ≥ 0.0.45 aplica `UTCDateTime` sozinho; **não** adicione `sa_type=DateTime(timezone=True)`.
- As duas tabelas se referenciam (`Relationship`). Se o Python reclamar de import circular entre os dois arquivos, use `TYPE_CHECKING` + string no type hint.

## Schema

```python
class RequisitionTable(SQLModel, table=True):
    __tablename__ = "requisition"
    id: int | None = Field(default=None, primary_key=True)       # "número da requisição"
    request_text: str = Field(max_length=1000)
    status: RequisitionStatus
    agent_message: str
    missing: list[str] = Field(default_factory=list, sa_type=JSON().with_variant(JSONB(), "postgresql"))
    currency: str = Field(default="USD", max_length=3)
    total_amount: Decimal = Field(max_digits=12, decimal_places=2)
    idempotency_key: str | None = Field(default=None, max_length=100, unique=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)
    items: list["RequisitionItemTable"] = Relationship(back_populates="requisition", cascade_delete=True)


class RequisitionItemTable(SQLModel, table=True):
    __tablename__ = "requisition_item"
    id: int | None = Field(default=None, primary_key=True)
    requisition_id: int = Field(foreign_key="requisition.id", ondelete="CASCADE", index=True)
    product_id: int
    title: str = Field(max_length=255)
    unit_price: Decimal = Field(max_digits=12, decimal_places=2)
    quantity: int = Field(gt=0)
    line_total: Decimal = Field(max_digits=12, decimal_places=2)
    requisition: RequisitionTable | None = Relationship(back_populates="items")
```

Decisões:
- O `id` é inteiro sequencial: o chat mostra "Requisição nº 42", mais legível que um UUID.
- **Dinheiro é `Decimal` em `NUMERIC(12,2)`**, nunca float. No domínio, é `Money`; o mapper converte.
- `title` e `unit_price` são um **snapshot** do momento da compra. O catálogo pode mudar depois.
- `line_total` e `total_amount` são calculados no agregado e gravados, o que permite auditar.
- `idempotency_key` única: um `POST` repetido com a mesma chave devolve a requisição existente.
- `CheckConstraint` via `__table_args__` para `quantity > 0` e `unit_price >= 0`.
- `RequisitionStatus` (StrEnum) mora em `schemas/requisition/` e é reutilizado pela tabela.

## Repositório e Unit of Work

```python
class SqlModelRequisitionRepository(RequisitionRepository):
    def __init__(self, session: Session, mapper: RequisitionTableMapper) -> None: ...

    def add(self, requisition: Requisition) -> None:
        self._session.add(self._mapper.to_table(requisition))

    def find_by_idempotency_key(self, key: str) -> Requisition | None: ...

    def list_recent(self, limit: int) -> list[Requisition]:
        statement = (select(RequisitionTable)
                     .options(selectinload(RequisitionTable.items))   # evita N+1
                     .order_by(RequisitionTable.created_at.desc())
                     .limit(limit))
        return [self._mapper.to_domain(row) for row in self._session.exec(statement).all()]


class SqlModelUnitOfWork(UnitOfWork):
    """Uma transação por caso de uso: requisição e itens gravados juntos, ou nada."""
    def __init__(self, database: Database, mapper: RequisitionTableMapper) -> None: ...
    def __enter__(self) -> Self: ...        # abre a Session e cria self.requisitions
    def __exit__(self, *exc) -> None: ...   # rollback se houve erro; fecha a Session
    def commit(self) -> None: ...
```

- O repositório recebe a `Session` (injeção). Quem abre e fecha a sessão é o Unit of Work.
- O mapper impede que a tabela vaze para o domínio. O repositório devolve sempre `Requisition` de `schemas/requisition/`.

## Engine e sessão (`Database`)

```python
class Database:
    def __init__(self, settings: Settings) -> None:
        self._engine = create_engine(str(settings.database_url), pool_pre_ping=True)

    def session(self) -> Session:
        return Session(self._engine)
```

## Migrations (Alembic): as tabelas são criadas automaticamente

1. `alembic.ini` na raiz do backend com `script_location = app/infrastructure/persistence/migrations`.
2. No `env.py`, `target_metadata = SQLModel.metadata` (importando os dois módulos de `tables/`) e a URL vinda de `Settings`.
3. No `script.py.mako`, adicione `import sqlmodel.sql.sqltypes`. Sem isso, as migrations autogeradas quebram ao referenciar `AutoString`.
4. Gere com `alembic revision --autogenerate -m "create requisition tables"` dentro de um container com acesso ao `db`, e **revise o arquivo** antes de commitar.
5. `scripts/prestart.sh` roda `alembic upgrade head` toda vez que o container sobe, antes do `fastapi run`.

**Não use `SQLModel.metadata.create_all()` em produção.** Só é aceitável em testes com SQLite.

## Inspeção com pgAdmin

http://localhost:5050 → servidor "compras" já registrado (`pgadmin/servers.json`) → senha do `POSTGRES_PASSWORD`.

## Testes

- Testes do repositório e do Unit of Work usam SQLite in-memory com `create_all`.
- A coluna `missing` usa `JSON().with_variant(JSONB(), "postgresql")`: JSONB no Postgres e JSON no SQLite.

## Checklist

- [ ] Dinheiro em `Decimal`/`NUMERIC(12,2)` e datas aware em UTC
- [ ] A migration foi revisada e o `prestart.sh` roda o upgrade
- [ ] Só se usa `session.exec(select(...))`, sem SQL concatenado
- [ ] O repositório devolve o agregado de `schemas/requisition/`, nunca linhas de tabela
- [ ] O `GET` usa `selectinload`, sem N+1
- [ ] `idempotency_key` com constraint única
