import pytest

from app.application.create_requisition_use_case import CreateRequisitionUseCase
from app.domain.errors.llm_timeout_error import LLMTimeoutError
from app.domain.errors.requisition_not_fulfillable_error import RequisitionNotFulfillableError
from app.domain.errors.requisition_not_saved_error import RequisitionNotSavedError
from app.schemas.agent.agent_run import AgentRun
from app.schemas.agent.draft_status import DraftStatus
from tests.fakes.agent_run_builder import AgentRunBuilder
from tests.fakes.fake_purchasing_agent import FakePurchasingAgent
from tests.fakes.in_memory_unit_of_work import InMemoryUnitOfWork
from tests.fakes.requisition_samples import RequisitionSamples

# Todos os testes do módulo são assíncronos e rodam com anyio.
pytestmark = pytest.mark.anyio


# Caso de uso com agente falso que, se agent_saves, grava como a tool criar_requisicao.
class UseCaseHarness:
    def __init__(self, run: AgentRun, *, agent_saves: bool) -> None:
        self.unit_of_work = InMemoryUnitOfWork()
        self.agent = FakePurchasingAgent(
            run,
            saves=RequisitionSamples.two_laptops() if agent_saves else None,
            unit_of_work=self.unit_of_work,
        )
        self.use_case = CreateRequisitionUseCase(self.agent, self.unit_of_work)


# Devolve a requisição gravada pela tool com a chave deste pedido e o rastro das tools.
async def test_returns_the_requisition_the_agent_saved_with_this_request_key() -> None:
    run = AgentRunBuilder().tool_call("buscar_produtos").tool_call("criar_requisicao").build()
    harness = UseCaseHarness(run, agent_saves=True)

    created = await harness.use_case.execute("1 macbook e 2 lenovos", "chave-1")

    assert harness.agent.requests[0].idempotency_key == "chave-1"
    assert created.requisition.idempotency_key == "chave-1"
    assert created.replayed is False
    assert [call.name for call in created.tool_calls] == ["buscar_produtos", "criar_requisicao"]


# Sem Idempotency-Key do cliente, gera uma chave e a repassa ao agente.
async def test_generates_a_key_when_the_client_sends_none() -> None:
    harness = UseCaseHarness(AgentRunBuilder().build(), agent_saves=True)

    created = await harness.use_case.execute("pedido")

    generated = harness.agent.requests[0].idempotency_key
    assert len(generated) == 32
    assert created.requisition.idempotency_key == generated


# Pedido impossível e nada gravado vira RequisitionNotFulfillableError com os faltantes.
async def test_unfulfillable_without_saving_is_not_fulfillable() -> None:
    run = AgentRunBuilder().status(DraftStatus.UNFULFILLABLE).missing("ferrari: não existe").build()
    harness = UseCaseHarness(run, agent_saves=False)

    with pytest.raises(RequisitionNotFulfillableError) as error:
        await harness.use_case.execute("uma ferrari")

    assert error.value.missing == ("ferrari: não existe",)


# Agente que diz "completo" sem ter chamado criar_requisicao gera RequisitionNotSavedError.
async def test_claiming_success_without_saving_is_an_error() -> None:
    run = AgentRunBuilder().status(DraftStatus.COMPLETE).tool_call("buscar_produtos").build()
    harness = UseCaseHarness(run, agent_saves=False)

    with pytest.raises(RequisitionNotSavedError) as error:
        await harness.use_case.execute("1 macbook")

    assert [call.name for call in error.value.tool_calls] == ["buscar_produtos"]


# Repetir a chave devolve a mesma requisição (replayed) sem rodar o agente de novo.
async def test_same_idempotency_key_does_not_run_the_agent_twice() -> None:
    harness = UseCaseHarness(AgentRunBuilder().build(), agent_saves=True)

    first = await harness.use_case.execute("pedido", "chave-1")
    second = await harness.use_case.execute("pedido", "chave-1")

    assert second.replayed is True
    assert second.requisition.id == first.requisition.id
    assert harness.agent.calls == 1


# Erros de domínio do agente, como timeout do LLM, sobem sem ser engolidos.
async def test_agent_errors_propagate() -> None:
    use_case = CreateRequisitionUseCase(
        FakePurchasingAgent(error=LLMTimeoutError()), InMemoryUnitOfWork()
    )

    with pytest.raises(LLMTimeoutError):
        await use_case.execute("1 macbook")
