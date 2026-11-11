import os

# app.main cria a aplicação no import: as variáveis obrigatórias precisam existir antes.
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("OPENROUTER_API_KEY", "test-key")
os.environ.setdefault("OPENROUTER_MODEL", "test/model")
os.environ.setdefault("INTERNAL_API_TOKEN", "token-interno-de-teste")
