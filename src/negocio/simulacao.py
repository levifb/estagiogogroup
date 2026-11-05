"""Compara políticas de fila a partir do estado em 30/09/2026, com 150 tratativas por dia útil.

Políticas:
- fifo: processo atual, por ordem de abertura da exceção;
- maior_valor: intuição comum, pedidos mais caros primeiro;
- maior_risco_hoje: maior perda esperada atual primeiro (parece certo, mas ignora quem vai piorar);
- otimizado: atribuição exata casos × dias (src/negocio/priorizacao.py).

S7: a simulação trata só o estoque de 2.000 exceções abertas. As novas aberturas dos
próximos dias entram no replanejamento diário e afetam todas as políticas por igual.
"""

from dataclasses import dataclass
from functools import lru_cache

import numpy as np
import pandas as pd

from src.dados.base import base_trabalho
from src.negocio import priorizacao as pr
from src.negocio.risco import CasoRisco, perda_esperada


@dataclass
class ResultadoPolitica:
    nome: str
    perda_total: float
    perda_por_dia: list[float]   # perda esperada dos casos tratados em cada dia
    dia: np.ndarray


@lru_cache(maxsize=1)
def casos_e_base() -> tuple[list[CasoRisco], pd.DataFrame]:
    df = base_trabalho()
    return [CasoRisco.da_linha(r) for r in df.itertuples(index=False)], df


def _resultado(nome: str, casos: list[CasoRisco], dia: np.ndarray) -> ResultadoPolitica:
    perdas = np.array([perda_esperada(c, int(t))["total"] for c, t in zip(casos, dia)])
    por_dia = [float(perdas[dia == d].sum()) for d in range(int(dia.max()) + 1)]
    return ResultadoPolitica(nome, float(perdas.sum()), por_dia, dia)


@lru_cache(maxsize=1)
def simular() -> dict[str, ResultadoPolitica]:
    casos, df = casos_e_base()
    perda_hoje = np.array([perda_esperada(c, 0)["total"] for c in casos])
    planos = {
        "fifo": pr.plano_fifo(df["data_abertura_excecao"]),
        "maior_valor": pr.plano_por_chave(df["valor"].to_numpy()),
        "maior_risco_hoje": pr.plano_por_chave(perda_hoje),
        "otimizado": pr.plano_otimo(casos, df["idade_dias"].tolist()),
    }
    return {nome: _resultado(nome, casos, dia) for nome, dia in planos.items()}
