"""Perfil da fila: volume, limpeza, ritmo de abertura, idade e valores."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analises._registro import Numero, br_int, br_pct, br_reais, imprimir  # noqa: E402
from src.dados.base import base_trabalho, relatorio_limpeza  # noqa: E402
from src.dados.fonte import carregar_excecoes  # noqa: E402

S = "analises/a01_perfil.py"
CAPACIDADE_DIA = 150  # parametros.md


def calcular() -> list[Numero]:
    bruto = carregar_excecoes()
    df = base_trabalho()
    rel = {r.regra[:2]: r.linhas_afetadas for r in relatorio_limpeza()}
    abertura = df["data_abertura_excecao"]
    dias = (abertura.max() - abertura.min()).days + 1
    por_dia = abertura.value_counts().sort_index()
    ult14 = por_dia[por_dia.index < "2026-09-30"].tail(14).mean()

    return [
        Numero("N01", len(df), br_int(len(df)), "exceções abertas únicas em 30/09/2026 (pedidos_excecao.csv sem duplicata order_id+tipo_excecao)", S),
        Numero("N02", len(bruto), br_int(len(bruto)), "linhas no arquivo pedidos_excecao.csv, antes da limpeza", S),
        Numero("N03", rel["R1"], br_int(rel["R1"]), "linhas duplicadas (mesmo order_id e tipo_excecao, status diferente) removidas", S),
        Numero("N04", rel["R2"], br_int(rel["R2"]), "exceções pagamento_pendente com status aguardando_transportadora (incoerente), marcadas", S),
        Numero("N05", len(df) / CAPACIDADE_DIA, f"{len(df) / CAPACIDADE_DIA:.1f}".replace(".", ","),
               "dias para zerar a fila na capacidade de 150 tratativas/dia, sem novas entradas (N01 / 150)", S),
        Numero("N06", len(df) / dias, f"{len(df) / dias:.0f}", f"exceções abertas por dia, em média, de {abertura.min():%d/%m} a {abertura.max():%d/%m/%Y} ({dias} dias)", S),
        Numero("N07", ult14, f"{ult14:.0f}", "exceções abertas por dia, média dos 14 dias antes de 30/09/2026", S),
        Numero("N08", int(por_dia.get("2026-09-30", 0)), br_int(por_dia.get("2026-09-30", 0)), "exceções abertas em 30/09/2026, a data de referência", S),
        Numero("N09", df["idade_dias"].median(), f"{df['idade_dias'].median():.0f} dias", "idade mediana das exceções abertas (30/09/2026 menos data_abertura_excecao)", S),
        Numero("N10", (df["idade_dias"] > 30).mean(), br_pct((df["idade_dias"] > 30).mean()), "exceções abertas há mais de 30 dias", S),
        Numero("N11", df["valor"].sum(), br_reais(df["valor"].sum()), "valor pago somado dos pedidos com exceção aberta", S),
        Numero("N12", df["valor"].median(), br_reais(df["valor"].median()), "valor mediano de um pedido com exceção", S),
        Numero("N13", df["valor"].quantile(0.95), br_reais(df["valor"].quantile(0.95)), "percentil 95 do valor do pedido com exceção", S),
        Numero("N14", int(df["cliente_alto_valor"].sum()), br_int(df["cliente_alto_valor"].sum()), "exceções de clientes com receita acumulada acima de R$ 1.500 (recompram em 70% dos casos)", S),
        Numero("N15", df["status"].isin(["aguardando_transportadora", "aguardando_cliente"]).mean(),
               br_pct(df["status"].isin(["aguardando_transportadora", "aguardando_cliente"]).mean()),
               "exceções paradas aguardando transportadora ou cliente", S),
    ]


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    imprimir(calcular())
    df = base_trabalho()
    print("\nPor tipo:\n", df["tipo_excecao"].value_counts().to_string())
    print("\nPor status:\n", df["status"].value_counts().to_string())
