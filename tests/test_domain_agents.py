from app.core.exceptions import InsufficientEvidence
from app.services.finance import answer_financial
from app.services.ombudsman import answer_ombudsman


def test_financial_paid_expenses_period(data_dir):
    answer, sources = answer_financial(
        "Quanto foi gasto em despesas pagas no período de janeiro a março de 2025?", data_dir
    )
    assert "R$ 305.937,01" in answer
    assert "27 registros" in answer
    assert sources[0].file == "financeiro/lancamentos_financeiros.csv"


def test_budget_highest_department_is_january_2026(data_dir):
    answer, sources = answer_financial("Qual departamento tem maior orçamento em janeiro de 2026?", data_dir)
    assert "janeiro de 2026" in answer
    assert "Tecnologia" in answer
    assert sources[0].file == "financeiro/orcamento_mensal.csv"


def test_revenue_total_for_2025(data_dir):
    answer, _ = answer_financial("Qual foi a soma de todas as receitas registradas em 2025?", data_dir)
    assert "R$ 275.727,70" in answer
    assert "6 registros" in answer


def test_financial_missing_type_asks_for_clarification(data_dir):
    try:
        answer_financial("Me mostre o financeiro em 2025", data_dir)
    except InsufficientEvidence as error:
        assert "receitas ou despesas" in str(error)
    else:
        raise AssertionError("Esperava esclarecimento sobre o tipo de lançamento")


def test_ombudsman_exact_protocol_and_missing(data_dir):
    known, source = answer_ombudsman("Qual o status do protocolo OUV-0002?", data_dir)
    missing, _ = answer_ombudsman("Existe o protocolo OUV-9999?", data_dir)
    assert "Aguardando área responsável" in known
    assert source[0].location == "OUV-0002"
    assert "Não encontrei" in missing


def test_ombudsman_enumerations_and_open_action_limit(data_dir):
    statuses, _ = answer_ombudsman("Quais status podem aparecer na Ouvidoria?", data_dir)
    opening, _ = answer_ombudsman("Como faço para abrir uma manifestação?", data_dir)
    assert "Aguardando área responsável" in statuses
    assert "não abre nem registra" in opening
