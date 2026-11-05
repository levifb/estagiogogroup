"""O checkout promete o prazo em dias corridos, mas o SLA contratado é em dias úteis."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analises._registro import Numero, br_int, br_pct, imprimir  # noqa: E402
from src.dados import calendario  # noqa: E402
from src.dados.base import base_trabalho  # noqa: E402

S = "analises/a02_prazo_prometido.py"


def calcular() -> list[Numero]:
    df = base_trabalho()
    corridos = [calendario.prazo_dias_corridos(d, s) for d, s in zip(df.data_pedido, df.sla_contratado_dias_uteis)]
    bate = (df["data_prometida"] == corridos)
    antecipa = (df["prazo_correto"] - df["data_prometida"]).dt.days
    atraso = df[df["tipo_excecao"] == "atraso_entrega"]
    no_sla = atraso["atraso_du_sla"] == 0
    return [
        Numero("N20", bate.mean(), br_pct(bate.mean()),
               "exceções em que data_prometida = data_pedido + 1 + SLA em dias CORRIDOS (parametros.md manda dias úteis)", S),
        Numero("N21", antecipa.median(), f"{antecipa.median():.0f} dias",
               "mediana de quantos dias corridos a data prometida ao cliente vem antes do prazo correto", S),
        Numero("N22", int(no_sla.sum()), br_int(no_sla.sum()),
               f"exceções atraso_entrega que estão dentro do SLA contratado em dias úteis (de {len(atraso)})", S),
        Numero("N23", no_sla.mean(), br_pct(no_sla.mean()),
               "parcela das exceções atraso_entrega que só existem porque o prazo prometido foi calculado em dias corridos", S),
    ]


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    imprimir(calcular())
