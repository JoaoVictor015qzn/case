from pydantic import BaseModel, ConfigDict

from app.schemas.requisition.requisition_item import RequisitionItem


class GroundingResult(BaseModel):
    """Resultado da verificação anti-invenção: itens aceitos e o motivo de cada recusa."""

    model_config = ConfigDict(frozen=True)

    accepted: tuple[RequisitionItem, ...]
    rejections: tuple[str, ...]

    @property
    def has_accepted_items(self) -> bool:
        return bool(self.accepted)

    @property
    def is_clean(self) -> bool:
        return not self.rejections
