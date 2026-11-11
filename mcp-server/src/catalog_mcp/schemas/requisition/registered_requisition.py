from catalog_mcp.schemas.pricing.money import Money
from catalog_mcp.schemas.requisition.camel_model import CamelModel


# Requisição como o backend a devolve após gravar: número, status e total.
class RegisteredRequisition(CamelModel):
    id: int
    status: str
    total: Money
