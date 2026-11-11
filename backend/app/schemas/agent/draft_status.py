from enum import StrEnum


class DraftStatus(StrEnum):
    """complete: tudo atendido; partial: parte atendida; unfulfillable: nada atende."""

    COMPLETE = "complete"
    PARTIAL = "partial"
    UNFULFILLABLE = "unfulfillable"
