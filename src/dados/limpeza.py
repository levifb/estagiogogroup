"""Regras de limpeza explícitas e contadas. Nada é corrigido em silêncio."""

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class RegraAplicada:
    regra: str
    linhas_afetadas: int
    efeito: str  # "removida" ou "marcada"
    exemplos: list = field(default_factory=list)


# Combinações de tipo e status que não fazem sentido operacional:
# um pagamento pendente não depende da transportadora.
_STATUS_INCOERENTE = {("pagamento_pendente", "aguardando_transportadora")}


def limpar(excecoes: pd.DataFrame) -> tuple[pd.DataFrame, list[RegraAplicada]]:
    df = excecoes.copy()
    relatorio: list[RegraAplicada] = []

    # R1: a mesma exceção (order_id + tipo) registrada duas vezes com status diferente.
    # Mantém a primeira ocorrência e marca que havia status em conflito.
    chave = ["order_id", "tipo_excecao"]
    dup_mask = df.duplicated(chave, keep="first")
    status_por_chave = df.groupby(chave)["status"].agg(lambda s: sorted(set(s)))
    removidas = df[dup_mask]
    relatorio.append(RegraAplicada(
        "R1 duplicata order_id+tipo_excecao", int(dup_mask.sum()), "removida",
        removidas["order_id"].head(5).tolist(),
    ))
    df = df[~dup_mask].copy()
    conflitos = df.set_index(chave).index.map(lambda k: len(status_por_chave[k]) > 1)
    df["status_em_conflito"] = list(conflitos)

    # R2: status incoerente com o tipo de exceção.
    incoerente = df.apply(lambda r: (r["tipo_excecao"], r["status"]) in _STATUS_INCOERENTE, axis=1)
    df["status_incoerente"] = incoerente
    relatorio.append(RegraAplicada(
        "R2 status incoerente com o tipo (pagamento_pendente aguardando transportadora)",
        int(incoerente.sum()), "marcada", df.loc[incoerente, "order_id"].head(5).tolist(),
    ))

    # R3: máquina preenchida só para Gocase (dicionário). Fora disso é erro de cadastro.
    eh_gocase = df["marca"].eq("Gocase")
    maquina_errada = (eh_gocase & df["maquina"].isna()) | (~eh_gocase & df["maquina"].notna())
    df["maquina_inconsistente"] = maquina_errada
    relatorio.append(RegraAplicada(
        "R3 máquina ausente em Gocase ou presente fora da Gocase", int(maquina_errada.sum()), "marcada",
        df.loc[maquina_errada, "order_id"].head(5).tolist(),
    ))

    return df.reset_index(drop=True), relatorio
