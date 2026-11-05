"""Base de trabalho: exceções limpas e enriquecidas com SLA, prazos, atraso e cliente.

É o que as outras camadas (negócio, agente, API) consomem.
"""

from functools import lru_cache

import pandas as pd

from src.dados import calendario
from src.dados.fonte import DATA_REFERENCIA, carregar_clientes, carregar_excecoes, carregar_transportadoras
from src.dados.limpeza import limpar

NORDESTE = {"BA", "PE", "CE", "RN", "PB", "MA", "AL", "PI", "SE"}


@lru_cache(maxsize=1)
def _base():
    exc, relatorio = limpar(carregar_excecoes())
    transp = carregar_transportadoras().rename(columns={"uf_atendida": "uf"})
    df = exc.merge(transp, on=["transportadora", "uf"], how="left", validate="many_to_one")
    df = df.merge(carregar_clientes(), on="customer_id", how="left", validate="many_to_one")

    df["prazo_correto"] = [calendario.prazo_correto(d, s) for d, s in zip(df.data_pedido, df.sla_contratado_dias_uteis)]
    fim = df["data_entrega"].fillna(DATA_REFERENCIA)
    df["entregue"] = df["data_entrega"].notna()
    df["atraso_du_prometido"] = [calendario.dias_uteis_atraso(p, f) for p, f in zip(df.data_prometida, fim)]
    df["atraso_du_sla"] = [calendario.dias_uteis_atraso(p, f) for p, f in zip(df.prazo_correto, fim)]
    df["nordeste"] = df["uf"].isin(NORDESTE)
    df["ticket_medio_cliente"] = df["receita_acumulada"] / df["n_pedidos"]
    df["cliente_alto_valor"] = df["receita_acumulada"] > 1500
    df["idade_dias"] = (DATA_REFERENCIA - df["data_abertura_excecao"]).dt.days
    return df, relatorio


def base_trabalho() -> pd.DataFrame:
    return _base()[0].copy()


def relatorio_limpeza():
    return list(_base()[1])
