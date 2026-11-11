#!/bin/sh
# Interrompe o start se qualquer comando falhar.
set -e

# Aplica todas as migrations pendentes antes de a API subir.
alembic upgrade head
