from __future__ import annotations

import calendar
import csv
import re
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

from app.core.exceptions import InsufficientEvidence
from app.models.schemas import Source
from app.services.classifier import _normalize

MONTHS = {
    "janeiro": 1,
    "fevereiro": 2,
    "marco": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
    "julho": 7,
    "agosto": 8,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "dezembro": 12,
}
MONTH_LABELS = {number: name.replace("marco", "março") for name, number in MONTHS.items()}

# (expressão, mês inicial, mês final, rótulo)
RANGES = (
    (r"\b(primeiro|1o|1)\s*(trimestre|tri)\b|\bq1\b", 1, 3, "1º trimestre"),
    (r"\b(segundo|2o|2)\s*(trimestre|tri)\b|\bq2\b", 4, 6, "2º trimestre"),
    (r"\b(terceiro|3o|3)\s*(trimestre|tri)\b|\bq3\b", 7, 9, "3º trimestre"),
    (r"\b(quarto|4o|4)\s*(trimestre|tri)\b|\bq4\b", 10, 12, "4º trimestre"),
    (r"\b(primeiro|1o|1)\s*semestre\b", 1, 6, "1º semestre"),
    (r"\b(segundo|2o|2)\s*semestre\b", 7, 12, "2º semestre"),
)

STATUS_TERMS = (
    (("em atraso", "atrasad", "vencid", "inadimpl"), "Atrasado"),
    (("pendente", "a pagar", "em aberto", "nao pago", "nao paga"), "Pendente"),
    (("pago", "paga", "pagos", "pagas", "realizad", "efetivamente"), "Pago"),
)

PAYMENT_TERMS = {
    "pix": "PIX",
    "boleto": "Boleto",
    "cartao": "Cartão corporativo",
    "transferencia": "Transferência",
}

GROUP_FIELDS = (
    (
        ("por departamento", "cada departamento", "qual departamento", "quais departamentos"),
        "departamento",
        "departamento",
    ),
    (
        ("por centro de custo", "cada centro de custo", "qual centro de custo", "quais centros de custo"),
        "centro_custo",
        "centro de custo",
    ),
    (("por categoria", "cada categoria", "qual categoria", "quais categorias"), "categoria", "categoria"),
    (("por status",), "status", "status"),
    (("por metodo de pagamento", "por forma de pagamento"), "metodo_pagamento", "método de pagamento"),
    (("por fornecedor", "qual fornecedor", "por contraparte"), "contraparte", "contraparte"),
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def _brl(value: Decimal) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _pct(numerator: Decimal, denominator: Decimal) -> str:
    if denominator == 0:
        return "n/d"
    return f"{(numerator / denominator * 100):.1f}%".replace(".", ",")


def _stem(word: str) -> str:
    return word[:-1] if len(word) > 4 and word.endswith("s") else word


@dataclass
class Period:
    start: str | None
    end: str | None
    name: str
    year: int | None = None
    months: tuple[int, int] | None = None

    def contains(self, date: str) -> bool:
        return not (self.start and self.end) or self.start <= date <= self.end


def parse_period(question: str) -> Period:
    q = _normalize(question)
    year_match = re.search(r"\b(20\d{2})\b", q)
    year = int(year_match.group(1)) if year_match else None
    if year is None:
        return Period(None, None, "todo o período disponível")
    for pattern, first, last, label in RANGES:
        if re.search(pattern, q):
            return Period(
                f"{year}-{first:02d}-01",
                f"{year}-{last:02d}-{calendar.monthrange(year, last)[1]:02d}",
                f"{label} de {year}",
                year,
                (first, last),
            )
    found = sorted({MONTHS[m.group(1)] for m in re.finditer(r"\b(" + "|".join(MONTHS) + r")\b", q)})
    if found:
        first, last = found[0], found[-1]
        name = (
            f"{MONTH_LABELS[first]} de {year}"
            if first == last
            else f"{MONTH_LABELS[first]} a {MONTH_LABELS[last]} de {year}"
        )
        return Period(
            f"{year}-{first:02d}-01",
            f"{year}-{last:02d}-{calendar.monthrange(year, last)[1]:02d}",
            name,
            year,
            (first, last),
        )
    return Period(f"{year}-01-01", f"{year}-12-31", str(year), year, (1, 12))


@dataclass
class Filters:
    centro_custo: str | None = None
    departamento: str | None = None
    categoria: str | None = None
    status: str | None = None
    metodo_pagamento: str | None = None
    contraparte: str | None = None
    applied: list[str] = field(default_factory=list)

    def match(self, row: dict[str, str]) -> bool:
        return all(
            expected is None or row[column] == expected
            for column, expected in (
                ("centro_custo", self.centro_custo),
                ("departamento", self.departamento),
                ("categoria", self.categoria),
                ("status", self.status),
                ("metodo_pagamento", self.metodo_pagamento),
                ("contraparte", self.contraparte),
            )
        )


def _category_for(q: str, categories: set[str]) -> str | None:
    words = {_stem(w) for w in re.findall(r"[a-z0-9]+", q)}
    matches = []
    for category in categories:
        normalized = _normalize(category)
        tokens = [t for t in re.findall(r"[a-z0-9]+", normalized) if len(t) > 3 and t not in {"receita", "despesa"}]
        if normalized in q or (tokens and _stem(tokens[0]) in words):
            matches.append(category)
    return matches[0] if len(matches) == 1 else None


def parse_filters(question: str, rows: list[dict[str, str]], *, include_status: bool = True) -> Filters:
    q = _normalize(question)
    filters = Filters()

    for code in re.findall(r"\bcc\s?-?(\d{3})\b", q):
        known = {row["centro_custo"] for row in rows}
        candidate = f"CC{code}"
        if candidate not in known:
            raise InsufficientEvidence(
                f"Não encontrei o centro de custo {candidate} na base. Disponíveis: {', '.join(sorted(known))}."
            )
        filters.centro_custo = candidate
        filters.applied.append(f"centro de custo {candidate}")

    for department in sorted({row["departamento"] for row in rows}):
        if re.search(rf"(?<![a-z0-9]){re.escape(_normalize(department))}(?![a-z0-9])", q) and not re.search(
            r"(?:por|cada|qual|quais)\s+departamento", q
        ):
            # "Marketing" é também categoria; só vira filtro de departamento se vier junto da palavra departamento/area.
            if re.search(
                rf"(departamento|area|time|equipe)\s+(de\s+|do\s+|da\s+)?{re.escape(_normalize(department))}", q
            ) or department not in {row["categoria"] for row in rows}:
                filters.departamento = department
                filters.applied.append(f"departamento {department}")
                break

    if filters.departamento != "Marketing" or "categoria" in q:
        category = _category_for(q, {row["categoria"] for row in rows})
        if category and not (filters.departamento and _normalize(category) == _normalize(filters.departamento)):
            filters.categoria = category
            filters.applied.append(f"categoria {category}")

    if include_status:
        for terms, status in STATUS_TERMS:
            if any(term in q for term in terms):
                filters.status = status
                filters.applied.append(f"status {status}")
                break

    for term, method in PAYMENT_TERMS.items():
        if re.search(rf"\b{term}\b", q):
            filters.metodo_pagamento = method
            filters.applied.append(f"pagamento via {method}")
            break

    for counterpart in sorted({row["contraparte"] for row in rows}):
        if _normalize(counterpart) in q:
            filters.contraparte = counterpart
            filters.applied.append(f"contraparte {counterpart}")
            break
    return filters


def _group_by(q: str) -> tuple[str, str] | None:
    for phrases, column, label in GROUP_FIELDS:
        if any(phrase in q for phrase in phrases):
            return column, label
    return None


def _scope(period: Period, filters: Filters) -> str:
    return "; ".join([f"período {period.name}", *filters.applied]) if filters.applied else f"período {period.name}"


def _budget_answer(question: str, q: str, data_dir: Path) -> tuple[str, list[Source]]:
    rows = _read_csv(data_dir / "financeiro" / "orcamento_mensal.csv")
    period = parse_period(question)
    filters = parse_filters(
        question,
        [{**r, "categoria": "", "status": "", "metodo_pagamento": "", "contraparte": ""} for r in rows],
        include_status=False,
    )
    filters.categoria = filters.status = filters.metodo_pagamento = filters.contraparte = None
    filters.applied = [item for item in filters.applied if item.startswith(("centro", "departamento"))]
    if period.year:
        rows = [row for row in rows if int(row["ano"]) == period.year]
    if period.months:
        rows = [row for row in rows if period.months[0] <= int(row["mes"]) <= period.months[1]]
    rows = [
        row
        for row in rows
        if filters.match({**row, "categoria": "", "status": "", "metodo_pagamento": "", "contraparte": ""})
    ]
    if not rows:
        raise InsufficientEvidence("Não encontrei orçamento para o período indicado.")
    column = "centro_custo" if "centro de custo" in q and not filters.centro_custo else "departamento"
    column_label = column.replace("_", " ").replace("centro custo", "centro de custo")
    totals: dict[str, Decimal] = {}
    for row in rows:
        totals[row[column]] = totals.get(row[column], Decimal("0")) + Decimal(row["orcamento_brl"])
    ranked = sorted(totals.items(), key=lambda item: item[1], reverse=True)
    grand = sum(totals.values(), Decimal("0"))
    scope = _scope(period, filters)
    if "maior" in q:
        answer = f"O {column_label} com maior orçamento ({scope}) é {ranked[0][0]}, com {_brl(ranked[0][1])}."
    elif "menor" in q:
        answer = f"O {column_label} com menor orçamento ({scope}) é {ranked[-1][0]}, com {_brl(ranked[-1][1])}."
    elif filters.applied and len(ranked) == 1:
        answer = f"O orçamento aprovado ({scope}) soma {_brl(grand)}."
    else:
        answer = (
            f"Orçamentos por {column_label} ({scope}): "
            + "; ".join(f"{n}: {_brl(v)}" for n, v in ranked)
            + f". Total: {_brl(grand)}."
        )
    source = Source(
        file="financeiro/orcamento_mensal.csv",
        location=period.name,
        excerpt=f"{scope}. {len(rows)} linhas de orçamento agrupadas por {column}. Total {_brl(grand)}.",
    )
    return answer + " Os valores são sintéticos.", [source]


def _execution_answer(question: str, data_dir: Path) -> tuple[str, list[Source]]:
    """Execução orçamentária = despesas realizadas (Pago) / orçamento aprovado do mesmo período e centro de custo."""
    ledger = _read_csv(data_dir / "financeiro" / "lancamentos_financeiros.csv")
    budget = _read_csv(data_dir / "financeiro" / "orcamento_mensal.csv")
    period = parse_period(question)
    filters = parse_filters(question, ledger, include_status=False)
    spent_rows = [
        r
        for r in ledger
        if r["tipo"] == "Despesa"
        and r["status"] == "Pago"
        and period.contains(r["data_competencia"])
        and (filters.centro_custo is None or r["centro_custo"] == filters.centro_custo)
        and (filters.departamento is None or r["departamento"] == filters.departamento)
    ]
    budget_rows = [
        r
        for r in budget
        if (period.year is None or int(r["ano"]) == period.year)
        and (period.months is None or period.months[0] <= int(r["mes"]) <= period.months[1])
        and (filters.centro_custo is None or r["centro_custo"] == filters.centro_custo)
        and (filters.departamento is None or r["departamento"] == filters.departamento)
    ]
    if not budget_rows:
        raise InsufficientEvidence("Não encontrei orçamento aprovado para o período/filtro informado.")
    spent = sum((Decimal(r["valor_brl"]) for r in spent_rows), Decimal("0"))
    planned = sum((Decimal(r["orcamento_brl"]) for r in budget_rows), Decimal("0"))
    scope = _scope(period, filters)
    answer = (
        f"Execução orçamentária ({scope}): {_pct(spent, planned)} — despesas pagas de {_brl(spent)} "
        f"({len(spent_rows)} lançamentos) sobre orçamento aprovado de {_brl(planned)}. "
        "Critério: despesas realizadas (status Pago) por data de competência. Os valores são sintéticos."
    )
    sources = [
        Source(
            file="financeiro/lancamentos_financeiros.csv",
            location=scope,
            excerpt=f"Despesas pagas: {_brl(spent)} em {len(spent_rows)} registros.",
        ),
        Source(
            file="financeiro/orcamento_mensal.csv",
            location=scope,
            excerpt=f"Orçamento aprovado: {_brl(planned)} em {len(budget_rows)} linhas.",
        ),
        Source(
            file="financeiro/indicadores_e_regras.json",
            location="Execução orçamentária",
            excerpt="Despesas realizadas divididas pelo orçamento aprovado do mesmo período e centro de custo.",
        ),
    ]
    return answer, sources


def _delinquency_answer(question: str, data_dir: Path) -> tuple[str, list[Source]]:
    """Inadimplência = receitas com status Atrasado / total de receitas registradas."""
    ledger = _read_csv(data_dir / "financeiro" / "lancamentos_financeiros.csv")
    period = parse_period(question)
    revenue = [r for r in ledger if r["tipo"] == "Receita" and period.contains(r["data_competencia"])]
    if not revenue:
        raise InsufficientEvidence("Não encontrei receitas no período informado para calcular a inadimplência.")
    total = sum((Decimal(r["valor_brl"]) for r in revenue), Decimal("0"))
    late = sum((Decimal(r["valor_brl"]) for r in revenue if r["status"] == "Atrasado"), Decimal("0"))
    late_count = sum(1 for r in revenue if r["status"] == "Atrasado")
    answer = (
        f"Inadimplência de recebíveis ({period.name}): {_pct(late, total)} — {_brl(late)} em receitas atrasadas "
        f"({late_count} de {len(revenue)} lançamentos) sobre {_brl(total)} de receitas registradas. Os valores são sintéticos."
    )
    sources = [
        Source(
            file="financeiro/lancamentos_financeiros.csv",
            location=period.name,
            excerpt=f"{len(revenue)} receitas; {late_count} com status Atrasado.",
        ),
        Source(
            file="financeiro/indicadores_e_regras.json",
            location="Inadimplência de recebíveis",
            excerpt="Receitas com status Atrasado divididas pelo total de receitas registradas.",
        ),
    ]
    return answer, sources


def answer_financial(question: str, data_dir: Path) -> tuple[str, list[Source]]:
    q = _normalize(question)
    if "inadimpl" in q:
        return _delinquency_answer(question, data_dir)
    if "execucao orcamentaria" in q:
        return _execution_answer(question, data_dir)
    if "orcamento" in q:
        return _budget_answer(question, q, data_dir)

    rows = _read_csv(data_dir / "financeiro" / "lancamentos_financeiros.csv")
    period = parse_period(question)
    if "receita" in q or "faturamento" in q:
        kind, label = "Receita", "receitas"
    elif any(term in q for term in ("despesa", "gast", "custo", "pago", "pagas")):
        kind, label = "Despesa", "despesas"
    else:
        raise InsufficientEvidence("Indique se deseja consultar receitas ou despesas.")

    filters = parse_filters(question, rows)
    rows = [r for r in rows if r["tipo"] == kind and period.contains(r["data_competencia"]) and filters.match(r)]
    if filters.status:
        label += {"Pago": " pagas", "Pendente": " pendentes", "Atrasado": " atrasadas"}[filters.status]
    if not rows:
        raise InsufficientEvidence(
            f"Não encontrei lançamentos de {label} para {_scope(period, filters)}. Confira o período e os filtros."
        )

    scope = _scope(period, filters)
    group = _group_by(q)
    if group is None and re.search(
        r"\b(maior|mais gast|mais)\b.*\b(departamento|categoria|centro de custo)\b|\b(departamento|categoria|centro de custo)\b.*\b(maior|mais)\b",
        q,
    ):
        for column, name in (
            ("departamento", "departamento"),
            ("categoria", "categoria"),
            ("centro_custo", "centro de custo"),
        ):
            if name in q:
                group = (column, name)
                break

    if group:
        column, group_label = group
        totals: dict[str, Decimal] = {}
        counts: dict[str, int] = {}
        for row in rows:
            totals[row[column]] = totals.get(row[column], Decimal("0")) + Decimal(row["valor_brl"])
            counts[row[column]] = counts.get(row[column], 0) + 1
        ranked = sorted(totals.items(), key=lambda item: item[1], reverse=True)
        grand = sum(totals.values(), Decimal("0"))
        if re.search(r"\b(qual|maior|mais)\b", q) and "por " not in q:
            name, value = ranked[0]
            answer = f"O {group_label} com maior total de {label} ({scope}) é {name}: {_brl(value)} em {counts[name]} registros (de {_brl(grand)} no total)."
        else:
            answer = (
                f"{label.capitalize()} por {group_label} ({scope}): "
                + "; ".join(f"{n}: {_brl(v)}" for n, v in ranked)
                + f". Total: {_brl(grand)} ({len(rows)} registros)."
            )
        excerpt = f"Agrupamento por {group_label} sobre {len(rows)} registros ({scope})."
    else:
        total = sum((Decimal(r["valor_brl"]) for r in rows), Decimal("0"))
        extra = f" Filtros aplicados: {', '.join(filters.applied)}." if filters.applied else ""
        if re.search(r"\b(media|medio)\b", q):
            average = total / len(rows)
            answer = f"O valor médio de {label} por data de competência em {period.name} é {_brl(average)} ({len(rows)} registros, total {_brl(total)}).{extra}"
        elif re.search(r"\bquant[oa]s\b|\bquantidade\b|\bnumero de\b", q):
            answer = f"Há {len(rows)} lançamentos de {label} por data de competência em {period.name}, somando {_brl(total)}.{extra}"
        else:
            answer = f"A soma de {label} por data de competência em {period.name} é {_brl(total)} ({len(rows)} registros).{extra}"
        excerpt = f"Filtro aplicado sobre {len(rows)} registros ({scope}). Total calculado com Decimal: {_brl(total)}."
    source = Source(
        file="financeiro/lancamentos_financeiros.csv", location=f"data_competencia: {scope}", excerpt=excerpt
    )
    return answer + " Os valores são sintéticos.", [source]
