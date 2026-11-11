from enum import StrEnum


# Situação da requisição salva: atendeu o pedido inteiro ou só parte dele.
class RequisitionStatus(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
