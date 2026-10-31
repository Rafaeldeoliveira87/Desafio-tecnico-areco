from fastapi import APIRouter

from app.models.schemas import AgentInfo, Category

router = APIRouter(tags=["agents"])


@router.get("/agents", response_model=list[AgentInfo])
def list_agents() -> list[AgentInfo]:
    return [
        AgentInfo(
            category=Category.FINANCEIRO,
            name="financial_agent",
            description="Consulta determinística a lançamentos e orçamentos.",
        ),
        AgentInfo(
            category=Category.INFORMACOES_INTERNAS,
            name="internal_information_agent",
            description="Recupera trechos de políticas, procedimentos e FAQ.",
        ),
        AgentInfo(
            category=Category.OUVIDORIA,
            name="ombudsman_agent",
            description="Consulta protocolos e informações enumeradas da base sintética.",
        ),
    ]
