"""Camada única de leitura de dados.

Único módulo do projeto que sabe que a fonte são CSVs. Para usar dados reais
(OMS, ERP, API das transportadoras), troque as funções `carregar_*` mantendo
as mesmas colunas e tipos de saída.
"""

from functools import lru_cache
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
PASTA_DADOS = RAIZ / "dados" / "operacoes"

# Data de referência do snapshot (parametros.md). Todo "hoje" do projeto é esta data.
DATA_REFERENCIA = pd.Timestamp("2026-09-30")

_DATAS_EXCECAO = ["data_pedido", "data_prometida", "data_entrega", "data_abertura_excecao"]


@lru_cache(maxsize=1)
def _excecoes_bruto() -> pd.DataFrame:
    df = pd.read_csv(PASTA_DADOS / "pedidos_excecao.csv", encoding="utf-8")
    for col in _DATAS_EXCECAO:
        df[col] = pd.to_datetime(df[col])
    df["brinde_no_pedido"] = df["brinde_no_pedido"].astype(str).str.lower().eq("true")
    return df


def carregar_excecoes() -> pd.DataFrame:
    """Exceções abertas, como estão no arquivo (com duplicatas). Use limpeza.limpar() para a base de trabalho."""
    return _excecoes_bruto().copy()


@lru_cache(maxsize=1)
def _clientes() -> pd.DataFrame:
    df = pd.read_csv(PASTA_DADOS / "clientes.csv", encoding="utf-8")
    df["data_primeiro_pedido"] = pd.to_datetime(df["data_primeiro_pedido"])
    return df


def carregar_clientes() -> pd.DataFrame:
    return _clientes().copy()


@lru_cache(maxsize=1)
def _transportadoras() -> pd.DataFrame:
    return pd.read_csv(PASTA_DADOS / "transportadoras.csv", encoding="utf-8")


def carregar_transportadoras() -> pd.DataFrame:
    return _transportadoras().copy()
