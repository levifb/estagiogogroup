"""Valor em risco hoje (30/09/2026) pelo modelo de src/negocio/risco.py."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from analises._registro import Numero, br_int, br_reais, imprimir  # noqa: E402
from src.negocio.risco import custo_de_espera, perda_esperada  # noqa: E402
from src.negocio.simulacao import casos_e_base  # noqa: E402

S = "analises/a04_valor_em_risco.py"


def calcular() -> list[Numero]:
    casos, df = casos_e_base()
    p0 = [perda_esperada(c, 0) for c in casos]
    tot = {k: sum(p[k] for p in p0) for k in ("reembolso", "recompra", "resolucao", "total")}
    espera1 = np.array([custo_de_espera(c, 0, 1) for c in casos])
    espera5 = np.array([custo_de_espera(c, 0, 5) for c in casos])
    entregue_atraso = int(((df["tipo_excecao"] == "atraso_entrega") & df["entregue"]).sum())
    return [
        Numero("N60", tot["total"], br_reais(tot["total"]),
               "perda esperada se todas as 2.000 exceções fossem tratadas hoje = reembolso esperado + recompra perdida + custo de resolução (SPEC.md S1–S6)", S, True),
        Numero("N61", tot["reembolso"], br_reais(tot["reembolso"]),
               "reembolso esperado hoje: soma de P(cancelamento pelos dias úteis de atraso contra o prometido) × valor pago", S, True),
        Numero("N62", tot["recompra"], br_reais(tot["recompra"]),
               "recompra perdida hoje: soma de P(cancelamento) × P(recompra 70% ou 28%) × 0,5 × ticket médio do cliente", S, True),
        Numero("N63", tot["resolucao"], br_reais(tot["resolucao"]),
               "custo de resolução hoje: soma de (1 − P(cancelamento)) × custo da ação padrão (reenvio = 24% do valor + frete)", S, True),
        Numero("N64", int((espera1 > 0).sum()), br_int((espera1 > 0).sum()),
               "exceções cuja perda esperada sobe se esperarem 1 dia útil (estão num degrau da tabela de cancelamento)", S),
        Numero("N65", espera1.sum(), br_reais(espera1.sum()),
               "quanto a perda esperada total sobe se nenhuma exceção for tratada amanhã (1 dia útil a mais)", S, True),
        Numero("N66", espera5.sum(), br_reais(espera5.sum()),
               "quanto a perda esperada total sobe se nenhuma exceção for tratada por 5 dias úteis", S, True),
        Numero("N67", entregue_atraso, br_int(entregue_atraso),
               "atrasos já entregues: o atraso parou de crescer, então tratar hoje ou depois não muda o risco", S),
    ]


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    imprimir(calcular())
