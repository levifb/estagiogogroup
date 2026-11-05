"""Padrões de causa raiz (src/dados/padroes.py) e os cruzamentos que os explicam."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from analises._registro import Numero, br_int, br_pct, br_reais, imprimir  # noqa: E402
from src.dados import padroes as P  # noqa: E402
from src.dados.base import base_trabalho  # noqa: E402

S = "analises/a03_padroes.py"


def calcular() -> list[Numero]:
    df = base_trabalho()
    ps = P.detectar(df)
    cobertos = set(o for p in ps for o in p.order_ids)
    valor_cob = df[df["order_id"].isin(cobertos)]["valor"].sum()
    out = [
        Numero("N30", len(ps), str(len(ps)),
               f"padrões de causa raiz detectados (mín. {P.MIN_CASOS} casos, taxa ≥ {P.MIN_RAZAO}× a base, recorte mais específico)", S),
        Numero("N31", len(cobertos), br_int(len(cobertos)), "exceções explicadas por algum padrão de causa raiz", S),
        Numero("N32", len(cobertos) / len(df), br_pct(len(cobertos) / len(df)), "parcela das exceções abertas explicada pelos padrões (N31 / N01)", S),
        Numero("N33", valor_cob, br_reais(valor_cob), "valor pago dos pedidos explicados pelos padrões", S),
    ]
    for i, p in enumerate(ps):
        out.append(Numero(
            f"N{40 + i}", p.casos, br_int(p.casos),
            f"{p.id} {p.dimensao}={p.valor} ({', '.join(p.tipos)}): {p.casos} de {p.exc_no_grupo} exceções do grupo "
            f"({br_pct(p.taxa_grupo)} contra {br_pct(p.taxa_base)} nos demais, {p.razao:.1f}×); {br_reais(p.valor_total)}", S))

    # Cruzamentos que explicam os padrões
    gc = df[df["maquina"].notna()]
    sem = gc.assign(sem=gc["data_pedido"].dt.to_period("W").dt.start_time)
    falha = sem[sem["tipo_excecao"] == "falha_personalizacao"]
    imp02_sem = falha[falha["maquina"] == "IMP-02"].groupby("sem").size()
    inicio = imp02_sem[imp02_sem >= 5].index.min()
    antes = falha[(falha["maquina"] == "IMP-02") & (falha["sem"] < inicio)]
    out.append(Numero("N50", 0, f"{inicio:%d/%m/%Y}",
                      "semana (data do pedido) em que as falhas de personalização da IMP-02 passam a 5 ou mais por semana", S))
    out.append(Numero("N51", len(antes), br_int(len(antes)), "falhas de personalização da IMP-02 antes dessa semana", S))

    cd2n = df[(df["cd"] == "CD2") & (df["turno"] == "noite") & (df["tipo_excecao"] == "item_faltante")]
    out.append(Numero("N52", cd2n["brinde_no_pedido"].mean(), br_pct(cd2n["brinde_no_pedido"].mean()),
                      "pedidos com brinde entre os itens faltantes do CD2 no turno da noite", S))
    out.append(Numero("N53", df["brinde_no_pedido"].mean(), br_pct(df["brinde_no_pedido"].mean()),
                      "pedidos com brinde entre todas as exceções (base de comparação para N52)", S))

    ent = df[df["entregue"]]
    re_ne = ent[(ent["transportadora"] == "Rota Express") & ent["nordeste"]]
    outros = ent[~((ent["transportadora"] == "Rota Express") & ent["nordeste"])]
    out.append(Numero("N54", re_ne["atraso_du_sla"].mean(), f"{re_ne['atraso_du_sla'].mean():.1f}".replace(".", ","),
                      "dias úteis médios além do SLA contratado nas entregas da Rota Express no Nordeste", S))
    out.append(Numero("N55", outros["atraso_du_sla"].mean(), f"{outros['atraso_du_sla'].mean():.1f}".replace(".", ","),
                      "dias úteis médios além do SLA contratado nas demais entregas (base de comparação para N54)", S))
    return out


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    imprimir(calcular())
    df = base_trabalho()
    for p in P.detectar(df):
        print(f"\n{p.id} {p.dimensao}={p.valor} por semana do pedido:", dict(list(p.semanas.items())))
    with pd.option_context("display.width", 200):
        f = df[df["tipo_excecao"] == "falha_personalizacao"]
        print("\nFalha de personalização por máquina e semana:\n",
              pd.crosstab(f["maquina"], f["data_pedido"].dt.to_period("W")).to_string())
