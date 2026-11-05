"""Ordem de chegada × otimizado, e o valor evitável das recomendações de processo."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from analises._registro import Numero, br_int, br_pct, br_reais, imprimir  # noqa: E402
from src.dados.padroes import detectar  # noqa: E402
from src.negocio.risco import perda_esperada  # noqa: E402
from src.negocio.simulacao import casos_e_base, simular  # noqa: E402

S = "analises/a05_simulacao.py"


def calcular() -> list[Numero]:
    r = simular()
    casos, df = casos_e_base()
    fifo, otim = r["fifo"].perda_total, r["otimizado"].perda_total
    piso = sum(perda_esperada(c, 0)["total"] for c in casos)
    out = [
        Numero("N70", fifo, br_reais(fifo), "perda esperada tratando o estoque em ordem de chegada, 150/dia útil (processo atual)", S, True),
        Numero("N71", otim, br_reais(otim), "perda esperada com o plano otimizado (atribuição exata casos × dias), 150/dia útil", S, True),
        Numero("N72", fifo - otim, br_reais(fifo - otim), "perda evitada pelo plano otimizado em relação à ordem de chegada (N70 − N71)", S, True),
        Numero("N73", (fifo - otim) / fifo, br_pct((fifo - otim) / fifo), "redução da perda esperada em relação à ordem de chegada", S, True),
        Numero("N74", (fifo - otim) / (fifo - piso), br_pct((fifo - otim) / (fifo - piso)),
               "parcela da perda evitável capturada pelo plano otimizado: (N70 − N71) / (N70 − N60); N60 seria tratar tudo hoje, o que não é possível", S, True),
        Numero("N75", r["maior_valor"].perda_total, br_reais(r["maior_valor"].perda_total), "perda esperada priorizando o maior valor de pedido (comparação)", S, True),
        Numero("N76", r["maior_risco_hoje"].perda_total, br_reais(r["maior_risco_hoje"].perda_total), "perda esperada priorizando a maior perda atual (comparação)", S, True),
    ]

    # Recomendações de processo: exceções acima da base, por mês, e o valor delas.
    # Período: datas de pedido no arquivo (parametros.md: pedidos de 01/08 a 27/09/2026).
    periodo = (df["data_pedido"].max() - df["data_pedido"].min()).days + 1
    por_mes = 30 / periodo
    perda0 = {c.order_id: perda_esperada(c, 0)["total"] for c in casos}
    excesso_total = 0.0
    padroes = detectar(df)
    cobertos = {o for p in padroes for o in p.order_ids}
    for i, p in enumerate(padroes):
        excesso_total += p.excesso
        media = np.mean([perda0[o] for o in p.order_ids])
        exc_mes = p.excesso * por_mes
        out.append(Numero(f"N{80 + 2 * i}", exc_mes, br_int(exc_mes),
                          f"{p.id} ({p.valor}): exceções por mês acima da taxa de base = excesso {p.excesso:.0f} × 30/{periodo} dias", S, True))
        out.append(Numero(f"N{81 + 2 * i}", exc_mes * media, br_reais(exc_mes * media),
                          f"{p.id} ({p.valor}): perda evitável por mês = exceções/mês acima da base × perda esperada média do padrão hoje ({br_reais(media)})", S, True))

    atraso = df[df["tipo_excecao"] == "atraso_entrega"]
    falsos = atraso[atraso["atraso_du_sla"] == 0]
    m = np.mean([perda0[o] for o in falsos["order_id"]])
    out.append(Numero("N95", len(falsos) * por_mes, br_int(len(falsos) * por_mes),
                      f"atrasos por mês que somem ao calcular o prazo prometido em dias úteis = N22 × 30/{periodo} dias", S, True))
    out.append(Numero("N96", len(falsos) * por_mes * m, br_reais(len(falsos) * por_mes * m),
                      f"perda esperada por mês desses atrasos (perda média hoje {br_reais(m)})", S, True))
    # Sem dupla contagem: atrasos falsos que já estão num padrão (ex.: Rota Express no Nordeste) ficam de fora.
    falsos_fora = int((~falsos["order_id"].isin(cobertos)).sum())
    evitaveis = (excesso_total + falsos_fora) * por_mes
    out.append(Numero("N97", evitaveis, br_int(evitaveis),
                      f"exceções por mês evitáveis mudando o processo: (excesso dos padrões {excesso_total:.0f} + {falsos_fora} atrasos falsos fora dos padrões) × 30/{periodo}", S, True))
    out.append(Numero("N98", evitaveis * 12 / 60, br_int(evitaveis * 12 / 60) + " h",
                      "horas do time por mês liberadas por N97, a 12 minutos por tratativa (parametros.md)", S, True))
    return out


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    imprimir(calcular())
