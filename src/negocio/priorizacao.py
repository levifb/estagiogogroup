"""Quais casos tratar em cada dia, com 150 tratativas por dia.

Formulação: cada caso j tratado no dia t custa perda_esperada(j, t). Toda tratativa
leva os mesmos 12 minutos, então cada dia tem 150 vagas iguais. Escolher o dia de
cada caso minimizando a soma das perdas é um problema de atribuição (casos × vagas),
resolvido de forma exata pelo algoritmo húngaro (scipy.optimize.linear_sum_assignment).

Por que não um guloso de um dia ("pega os 150 que mais pioram amanhã")? A tabela de
cancelamento é em degraus: um caso com 1 dia de atraso não piora amanhã (fica em 4%),
mas salta para 10% depois de amanhã. O guloso de um dia adia esse caso e paga o salto;
a atribuição olha o horizonte inteiro.
"""

import math

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment

from src.negocio.risco import CasoRisco, perda_esperada

CAPACIDADE_DIA = 150          # parametros.md
PRAZO_MAX_ALTO_VALOR = 2      # S4: cliente com receita > R$ 1.500 é tratado até o 2º dia útil (dias 0 a 2)
PENALIDADE = 1e6


def matriz_perdas(casos: list[CasoRisco], horizonte: int) -> np.ndarray:
    return np.array([[perda_esperada(c, t)["total"] for t in range(horizonte)] for c in casos])


def horizonte_para(n_casos: int, capacidade: int = CAPACIDADE_DIA) -> int:
    return math.ceil(n_casos / capacidade)


def plano_otimo(casos: list[CasoRisco], idade_dias: list[int], capacidade: int = CAPACIDADE_DIA) -> np.ndarray:
    """Dia (0, 1, 2...) em que cada caso deve ser tratado, minimizando a perda esperada total.

    Regras além da perda (suposições do SPEC.md):
    - S4: clientes acima de R$ 1.500 entram até o dia PRAZO_MAX_ALTO_VALOR.
    - S6 (envelhecimento): entre casos de perda igual, o mais antigo vai primeiro.
      É um desempate de centavos, que nunca troca R$ de perda por idade.
    """
    H = horizonte_para(len(casos), capacidade)
    L = matriz_perdas(casos, H)
    idade = np.asarray(idade_dias, dtype=float)
    desempate = 1e-4 * (idade / max(idade.max(), 1))[:, None] * np.arange(H)[None, :]
    custo = L + desempate
    for i, c in enumerate(casos):
        if c.alto_valor:
            custo[i, PRAZO_MAX_ALTO_VALOR + 1:] += PENALIDADE
    vagas = np.repeat(custo, capacidade, axis=1)          # cada dia vira `capacidade` colunas
    linhas, colunas = linear_sum_assignment(vagas)
    dia = np.empty(len(casos), dtype=int)
    dia[linhas] = colunas // capacidade
    return dia


def plano_fifo(data_abertura: pd.Series, capacidade: int = CAPACIDADE_DIA) -> np.ndarray:
    """Processo atual: ordem de chegada (data de abertura da exceção, mais antiga primeiro)."""
    ordem = np.argsort(data_abertura.values, kind="stable")
    dia = np.empty(len(ordem), dtype=int)
    dia[ordem] = np.arange(len(ordem)) // capacidade
    return dia


def plano_por_chave(chave: np.ndarray, capacidade: int = CAPACIDADE_DIA) -> np.ndarray:
    """Ordena por uma chave decrescente (ex.: valor do pedido). Serve de comparação."""
    ordem = np.argsort(-np.asarray(chave), kind="stable")
    dia = np.empty(len(ordem), dtype=int)
    dia[ordem] = np.arange(len(ordem)) // capacidade
    return dia


def perda_do_plano(casos: list[CasoRisco], dia: np.ndarray) -> float:
    return float(sum(perda_esperada(c, int(t))["total"] for c, t in zip(casos, dia)))
