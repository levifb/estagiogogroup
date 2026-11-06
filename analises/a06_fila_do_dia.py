"""Decisões da fila do dia (150 casos) conferidas contra a tabela de política do SPEC.md, por modelo.

É uma checagem automática: o rótulo vem de eval/montar_gabarito.rotular(), a mesma tabela
que propôs o gabarito, e não de uma revisão humana caso a caso.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analises._registro import Numero, br_int, imprimir  # noqa: E402
from eval.mensagens import checar  # noqa: E402
from eval.montar_gabarito import rotular  # noqa: E402
from src.agente.ficha import fila_do_dia, montar_ficha  # noqa: E402
from src.agente.pipeline import carregar_prompt, ler_cache  # noqa: E402

S = "analises/a06_fila_do_dia.py"


def calcular() -> list[Numero]:
    versao, _, _ = carregar_prompt("decisao")
    fila = fila_do_dia()
    n = humano = ok = msg_ok = com_msg = 0
    por_modelo: dict[str, int] = {}
    for o in fila:
        f = montar_ficha(o)
        r = ler_cache(o, f["excecao"]["tipo"], versao)
        if r is None or r.decisao_modelo is None:
            continue
        n += 1
        modelo = (r.modelo or "openai/gpt-oss-120b").split("/")[-1]
        por_modelo[modelo] = por_modelo.get(modelo, 0) + 1
        humano += r.vai_para_humano
        ok += r.acao_final.value in rotular(r.ficha)["acoes_aceitaveis"]
        d = r.decisao_modelo
        if d.acao.value not in ("aguardar", "escalar_humano"):
            com_msg += 1
            msg_ok += not checar(r.ficha, d.acao.value, d.mensagem_cliente)
    modelos = ", ".join(f"{k}: {v}" for k, v in sorted(por_modelo.items()))
    return [
        Numero("N100", n, br_int(n), f"casos da fila do dia com decisão do modelo (de {len(fila)}); por modelo: {modelos}", S),
        Numero("N101", ok, br_int(ok), "decisões da fila do dia que batem com a tabela de política do SPEC (checagem automática)", S),
        Numero("N102", humano, br_int(humano), "casos da fila do dia enviados à analista pelas regras H1–H7", S),
        Numero("N103", msg_ok, br_int(msg_ok), f"mensagens ao cliente da fila do dia sem problema nas checagens automáticas (de {com_msg})", S),
    ]


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    imprimir(calcular())
