"""Modelo de risco e priorização, com contas feitas à mão.

Data de referência: quarta 30/09/2026 (t = 0). t = 1 é quinta 01/10.
Prazo prometido segunda 28/09 → em 30/09 o atraso é 2 dias úteis (29 e 30).
"""

import numpy as np
import pandas as pd
import pytest

from src.negocio import priorizacao as pr
from src.negocio.risco import CasoRisco, custo_de_espera, perda_esperada, prob_cancelamento

T = pd.Timestamp


def caso(order_id="X", tipo="avaria_transporte", valor=100.0, frete=10.0, entregue=True,
         prometida="2026-09-28", atraso_atual=2, ticket=100.0, alto_valor=False):
    return CasoRisco(order_id, tipo, valor, frete, entregue, T(prometida), atraso_atual, ticket, alto_valor)


@pytest.mark.parametrize("dias, p", [(0, 0), (1, .04), (2, .04), (3, .10), (5, .10), (6, .22), (10, .22), (11, .40), (30, .40)])
def test_tabela_de_cancelamento(dias, p):
    assert prob_cancelamento(dias) == p


def test_perda_esperada_conta_a_mao():
    # avaria, 2 dias úteis de atraso hoje → P = 4%
    # reembolso = 0,04 × 100 = 4,00
    # recompra = 0,04 × 0,28 × 0,5 × 100 = 0,56
    # resolução = 0,96 × (0,24 × 100 + 10) = 32,64
    p = perda_esperada(caso(), 0)
    assert p["p_cancelamento"] == 0.04
    assert p["reembolso"] == pytest.approx(4.0)
    assert p["recompra"] == pytest.approx(0.56)
    assert p["resolucao"] == pytest.approx(32.64)
    assert p["total"] == pytest.approx(37.20)


def test_custo_de_espera_no_degrau():
    # amanhã o atraso vira 3 dias → P = 10%
    # total amanhã = 10 + 0,10×14 + 0,90×34 = 10 + 1,4 + 30,6 = 42,0 → espera custa 4,80
    assert custo_de_espera(caso(), 0) == pytest.approx(42.0 - 37.2)


def test_atraso_ja_entregue_nao_piora():
    c = caso(tipo="atraso_entrega", entregue=True, atraso_atual=4)
    assert perda_esperada(c, 0)["total"] == perda_esperada(c, 10)["total"]


def test_alto_valor_usa_recompra_de_70():
    p = perda_esperada(caso(alto_valor=True), 0)
    assert p["recompra"] == pytest.approx(0.04 * 0.70 * 0.5 * 100)


def test_otimo_trata_hoje_quem_esta_no_degrau():
    # capacidade 1/dia. A está no degrau (2 → 3 dias amanhã). B já está no teto de 40% e não piora.
    a = caso("A")
    b = caso("B", prometida="2026-09-01", atraso_atual=21)
    dia = pr.plano_otimo([b, a], idade_dias=[0, 0], capacidade=1)
    assert list(dia) == [1, 0]


def test_otimo_olha_alem_de_amanha():
    # capacidade 1/dia, 3 casos, 3 dias.
    # A: atraso 1 hoje (P 4%), 2 amanhã (4%), 3 depois (10%) → só piora no dia 2.
    # B: no degrau, piora já amanhã (2 → 3).
    # C: no teto, nunca piora.
    # Guloso de um dia trataria B hoje e depois A ou C ao acaso; o ótimo garante A no dia 1 e C por último.
    a = caso("A", prometida="2026-09-29", atraso_atual=1)
    b = caso("B")
    c = caso("C", prometida="2026-09-01", atraso_atual=21)
    dia = pr.plano_otimo([a, b, c], idade_dias=[0, 0, 0], capacidade=1)
    assert list(dia) == [1, 0, 2]


def test_alto_valor_respeita_prazo_maximo():
    # 4 casos no teto (perda igual em qualquer dia) e capacidade 1: o cliente de alto valor entra até o dia 2.
    teto = dict(prometida="2026-09-01", atraso_atual=21)
    casos = [caso(f"C{i}", **teto) for i in range(3)] + [caso("VIP", alto_valor=True, **teto)]
    dia = pr.plano_otimo(casos, idade_dias=[50, 40, 30, 0], capacidade=1)
    assert dia[3] <= pr.PRAZO_MAX_ALTO_VALOR


def test_empate_vai_para_o_mais_antigo():
    teto = dict(prometida="2026-09-01", atraso_atual=21)
    dia = pr.plano_otimo([caso("NOVO", **teto), caso("VELHO", **teto)], idade_dias=[1, 40], capacidade=1)
    assert list(dia) == [1, 0]


def test_fifo_segue_ordem_de_abertura():
    abertura = pd.Series(pd.to_datetime(["2026-09-10", "2026-08-01", "2026-09-01"]))
    assert list(pr.plano_fifo(abertura, capacidade=1)) == [2, 0, 1]


def test_otimo_nunca_perde_para_fifo_no_estoque_real():
    from src.negocio.simulacao import simular
    r = simular()
    assert r["otimizado"].perda_total <= r["fifo"].perda_total
    assert np.bincount(r["otimizado"].dia).max() <= pr.CAPACIDADE_DIA


def test_pagamento_pendente_nao_gera_reembolso():
    # o cliente não pagou: cancelar não devolve dinheiro, só perde a recompra
    p = perda_esperada(caso(tipo="pagamento_pendente", entregue=False), 0)
    assert p["reembolso"] == 0
    assert p["recompra"] > 0
