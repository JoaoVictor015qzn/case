from catalog_mcp.schemas.requisition.camel_model import CamelModel
from catalog_mcp.schemas.requisition.registered_requisition import RegisteredRequisition


# Resposta do backend; replayed indica que a chave de idempotência já tinha sido usada.
class RegistrationResponse(CamelModel):
    requisition: RegisteredRequisition
    replayed: bool = False
