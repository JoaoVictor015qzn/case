from enum import StrEnum


# Moedas suportadas; a DummyJSON só trabalha com dólar.
class Currency(StrEnum):
    USD = "USD"
