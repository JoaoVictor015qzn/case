from abc import ABC, abstractmethod

from catalog_mcp.schemas.requisition.registration_response import RegistrationResponse
from catalog_mcp.schemas.requisition.requisition_submission import RequisitionSubmission


# Port de gravação de requisições; a implementação real chama o endpoint interno do backend.
class RequisitionRegistry(ABC):
    @abstractmethod
    async def register(self, submission: RequisitionSubmission) -> RegistrationResponse:
        """Grava a requisição no backend. Levanta RequisitionRejectedError se ela for recusada."""
