"""Regras de prazo de dados/operacoes/parametros.md.

Calendário de referência: 07/08/2026 é sexta; 07/09/2026 (segunda) é feriado.
"""

import pandas as pd
import pytest

from src.dados import calendario as cal

T = pd.Timestamp


@pytest.mark.parametrize("pedido, separacao", [
    ("2026-08-12", "2026-08-13"),  # quarta → quinta
    ("2026-08-14", "2026-08-17"),  # sexta → segunda (exemplo do parâmetro)
    ("2026-08-15", "2026-08-17"),  # sábado → segunda
    ("2026-08-16", "2026-08-17"),  # domingo → segunda
    ("2026-09-04", "2026-09-08"),  # sexta antes do feriado de 07/09 → terça
    ("2026-09-06", "2026-09-08"),  # domingo antes do feriado → terça
])
def test_dia_de_separacao(pedido, separacao):
    assert cal.dia_separacao(pedido) == T(separacao)


def test_prazo_correto_conta_dias_uteis():
    # quarta 12/08: separação qui 13; +3 dias úteis = sex 14, seg 17, ter 18
    assert cal.prazo_correto("2026-08-12", 3) == T("2026-08-18")


def test_prazo_correto_pula_feriado():
    # sexta 04/09: separação ter 08/09 (07 é feriado); +2 = qua 09, qui 10
    assert cal.prazo_correto("2026-09-04", 2) == T("2026-09-10")


def test_prazo_dias_corridos_reproduz_o_sistema_atual():
    # caso real: GC7004826, pedido 12/08, SLA 3, data_prometida no arquivo = 16/08
    assert cal.prazo_dias_corridos("2026-08-12", 3) == T("2026-08-16")


@pytest.mark.parametrize("prazo, fim, esperado", [
    ("2026-08-18", "2026-08-18", 0),  # entregou no dia
    ("2026-08-18", "2026-08-17", 0),  # adiantado
    ("2026-08-18", "2026-08-19", 1),
    ("2026-08-14", "2026-08-17", 1),  # prazo sexta, entrega segunda: 1 dia útil
    ("2026-08-16", "2026-08-17", 1),  # prazo domingo (dias corridos), entrega segunda
    ("2026-09-04", "2026-09-08", 1),  # sexta → terça, com feriado na segunda
    ("2026-08-14", "2026-08-15", 1),  # prazo sexta, entrega sábado: atrasou (suposição S-cal-1)
    ("2026-08-14", "2026-08-19", 3),  # sexta → quarta: seg, ter, qua
])
def test_dias_uteis_atraso(prazo, fim, esperado):
    assert cal.dias_uteis_atraso(prazo, fim) == esperado
