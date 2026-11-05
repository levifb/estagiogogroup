"""Detecção de concentrações de causa raiz.

Limitação importante: o arquivo só tem pedidos COM exceção, não o total de
pedidos por máquina, turno ou transportadora. Por isso a "taxa" aqui é a
proporção de um tipo de exceção entre as exceções do grupo, comparada com a
mesma proporção nos demais grupos. Não é a incidência sobre todos os pedidos.
"""

from dataclasses import dataclass, field

import pandas as pd

# Dimensões testadas. Combinações explicam padrões que uma coluna sozinha esconde.
DIMENSOES: dict[str, list[str]] = {
    "maquina": ["maquina"],
    "turno": ["turno"],
    "cd": ["cd"],
    "cd+turno": ["cd", "turno"],
    "lote": ["lote_produto"],
    "sku": ["sku"],
    "sku+lote": ["sku", "lote_produto"],
    "marca": ["marca"],
    "transportadora": ["transportadora"],
    "transportadora+regiao": ["transportadora", "regiao"],
    "transportadora+uf": ["transportadora", "uf"],
    "brinde": ["brinde_no_pedido"],
}

# Limiares (registrados em docs/NUMEROS.md junto com os padrões).
MIN_CASOS = 20        # volume mínimo de exceções do tipo no grupo
MIN_RAZAO = 2.5       # taxa no grupo / taxa de base
MAX_SOBREPOSICAO = 0.5  # padrão novo é descartado se metade dos casos já está num padrão aceito


@dataclass
class Padrao:
    id: str
    dimensao: str
    valor: str
    tipos: list[str]
    casos: int
    exc_no_grupo: int
    taxa_grupo: float
    taxa_base: float
    razao: float
    excesso: float  # casos acima do esperado pela taxa de base
    valor_total: float
    order_ids: list[str] = field(repr=False)
    semanas: dict[str, int] = field(repr=False)  # semana de data_pedido → casos


def _candidatos(df: pd.DataFrame) -> list[dict]:
    df = df.assign(regiao=df["nordeste"].map({True: "Nordeste", False: "Outras"}))
    out = []
    for nome, cols in DIMENSOES.items():
        # A base é calculada só onde a dimensão existe (ex.: máquina só em pedidos Gocase).
        sub = df.dropna(subset=cols)
        total_por_tipo = sub["tipo_excecao"].value_counts()
        n = len(sub)
        chave = sub[cols].astype(str).agg(" | ".join, axis=1)
        tam = chave.value_counts()
        cont = pd.crosstab(chave, sub["tipo_excecao"])
        for valor, linha in cont.iterrows():
            g = tam[valor]
            for tipo, c in linha.items():
                if c < MIN_CASOS:
                    continue
                base = (total_por_tipo[tipo] - c) / (n - g) if n > g else 0
                taxa = c / g
                if base == 0 or taxa / base < MIN_RAZAO:
                    continue
                mask = (chave == valor) & (sub["tipo_excecao"] == tipo)
                out.append(dict(dimensao=nome, valor=valor, tipo=tipo, casos=int(c), exc_no_grupo=int(g),
                                taxa_grupo=taxa, taxa_base=base, razao=taxa / base,
                                excesso=c - base * g, idx=set(sub.index[mask])))
    return out


FRACAO_EXCESSO_REFINO = 0.8  # o refinamento precisa explicar 80% do excesso do grupo amplo


def _mais_especifico(c: dict, candidatos: list[dict]) -> dict:
    """Troca um grupo amplo (ex.: 'CD2') por um recorte dele que explica quase todo o excesso
    (ex.: 'CD2 | noite'). O recorte é o que tem dono e ação; o grupo amplo só dilui a evidência."""
    refinos = [r for r in candidatos
               if r is not c and r["tipo"] == c["tipo"] and r["idx"] < c["idx"]
               and r["excesso"] >= FRACAO_EXCESSO_REFINO * c["excesso"]]
    return max(refinos, key=lambda r: r["razao"], default=c)


def detectar(df: pd.DataFrame) -> list[Padrao]:
    """Recebe a base de trabalho (src.dados.base) e devolve os padrões aceitos, do maior excesso para o menor."""
    candidatos = _candidatos(df)
    aceitos: list[dict] = []
    cobertos: set = set()
    for c in sorted(candidatos, key=lambda c: -c["excesso"]):
        if len(c["idx"] & cobertos) > MAX_SOBREPOSICAO * len(c["idx"]):
            continue
        c = _mais_especifico(c, candidatos)
        if len(c["idx"] & cobertos) > MAX_SOBREPOSICAO * len(c["idx"]):
            continue
        # O padrão precisa se sustentar só com os casos que nenhum padrão aceito explica
        # (ex.: um SKU com falhas que, na verdade, eram da máquina IMP-02).
        residuo = c["idx"] - cobertos
        if len(residuo) < MIN_CASOS or (len(residuo) / c["exc_no_grupo"]) / c["taxa_base"] < MIN_RAZAO:
            continue
        aceitos.append(c)
        cobertos |= c["idx"]

    # Junta tipos diferentes com a mesma dimensão e valor (ex.: atraso e rastreio parado na mesma rota).
    agrupado: dict[tuple, list[dict]] = {}
    for c in aceitos:
        agrupado.setdefault((c["dimensao"], c["valor"]), []).append(c)

    padroes = []
    for (dim, valor), itens in sorted(agrupado.items(), key=lambda kv: -sum(i["excesso"] for i in kv[1])):
        idx = sorted(set().union(*(i["idx"] for i in itens)))
        linhas = df.loc[idx]
        casos = len(idx)
        g = itens[0]["exc_no_grupo"]
        base = sum(i["taxa_base"] * g for i in itens) / g
        semanas = linhas["data_pedido"].dt.to_period("W").astype(str).value_counts().sort_index()
        padroes.append(Padrao(
            id=f"P{len(padroes) + 1:02d}", dimensao=dim, valor=valor,
            tipos=[i["tipo"] for i in itens], casos=casos, exc_no_grupo=g,
            taxa_grupo=casos / g, taxa_base=base, razao=(casos / g) / base if base else float("inf"),
            excesso=sum(i["excesso"] for i in itens), valor_total=float(linhas["valor"].sum()),
            order_ids=linhas["order_id"].tolist(), semanas=semanas.to_dict(),
        ))
    return padroes
