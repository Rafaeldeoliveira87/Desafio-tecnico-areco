import pytest

from app.core.exceptions import InsufficientEvidence
from app.models.schemas import Category
from app.services.classifier import classify_local
from app.services.finance import answer_financial, parse_period


def test_cost_center_filter_is_applied_and_declared(data_dir):
    answer, _ = answer_financial("Quanto foi gasto em despesas do centro de custo CC100 em 2025?", data_dir)
    assert "R$ 234.196,14" in answer
    assert "22 registros" in answer
    assert "centro de custo CC100" in answer


def test_unknown_cost_center_is_not_silently_ignored(data_dir):
    with pytest.raises(InsufficientEvidence) as error:
        answer_financial("Despesas do centro de custo CC999", data_dir)
    assert "CC999" in str(error.value)


def test_category_filter(data_dir):
    answer, _ = answer_financial("Quanto gastamos com viagens em 2025?", data_dir)
    assert "R$ 158.492,48" in answer
    assert "categoria Viagens" in answer


def test_group_by_department_ranking(data_dir):
    answer, _ = answer_financial("Qual departamento mais gastou em 2025?", data_dir)
    assert "Marketing" in answer
    assert "R$ 329.703,64" in answer


def test_budget_execution_indicator(data_dir):
    answer, sources = answer_financial("Qual a execução orçamentária da Tecnologia em 2025?", data_dir)
    assert "28,4%" in answer
    assert {s.file for s in sources} >= {
        "financeiro/lancamentos_financeiros.csv",
        "financeiro/orcamento_mensal.csv",
        "financeiro/indicadores_e_regras.json",
    }


def test_delinquency_indicator(data_dir):
    answer, _ = answer_financial("Qual a inadimplência de recebíveis?", data_dir)
    assert "5,6%" in answer
    assert "1 de 17" in answer


def test_quarter_and_accented_month_labels():
    assert parse_period("despesas no primeiro trimestre de 2025").name == "1º trimestre de 2025"
    assert parse_period("de janeiro a março de 2025").name == "janeiro a março de 2025"


def test_mixed_domain_tie_break_by_intent():
    assert classify_local("Quero reembolso de uma despesa de viagem").category == Category.INFORMACOES_INTERNAS
    assert classify_local("Quanto gastamos com reembolso de viagens em 2025?").category == Category.FINANCEIRO


def test_cost_center_code_routes_to_finance():
    assert classify_local("Quanto gastou o CC200?").category == Category.FINANCEIRO
