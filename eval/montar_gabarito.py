"""Sorteia os casos do gabarito e propõe o rótulo de cada um pela política do SPEC.md.

Os rótulos saem com anotado_por = "claude_pendente_levi". O Levi revisa cada linha
(muda para "claude_revisado_por_levi" ou corrige e marca "levi") antes de o número
do eval ir para o README.

Uso: python -m eval.montar_gabarito   (não sobrescreve um gabarito já revisado)
"""

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

import pandas as pd  # noqa: E402

from src.agente.ficha import montar_ficha  # noqa: E402
from src.agente.pipeline import carregar_prompt  # noqa: E402
from src.agente.regras import regra_humano  # noqa: E402
from src.dados.base import base_trabalho  # noqa: E402

SEMENTE = 42
ARQ = RAIZ / "eval" / "gabarito.jsonl"


def rotular(f: dict) -> dict:
    """Aplica a tabela 'Política de ações' do SPEC.md. Devolve ação final esperada e racional."""
    exc, ent = f["excecao"], f["entrega"]
    tipo, status = exc["tipo"], exc["status"]
    regra = regra_humano(f, _sem_decisao())
    if regra and regra[0] != "H6":
        return dict(acao_esperada="escalar_humano", acoes_aceitaveis=["escalar_humano"], deve_ir_para_humano=True,
                    motivo_humano_esperado=regra[0], racional=f"SPEC.md, regra {regra[0]}: {regra[1]}")
    if tipo == "atraso_entrega" and ent["entregue"]:
        a, ac, rac = "contatar_cliente", [], "atraso já entregue: o atraso parou de crescer; pedido de desculpas, sem custo"
    elif tipo == "atraso_entrega" and ent["dentro_do_sla_contratado"]:
        a, ac, rac = "contatar_cliente", [], "dentro do SLA contratado: o erro é a data prometida em dias corridos; informar o prazo correto"
    elif status == "aguardando_cliente":
        a, ac, rac = "contatar_cliente", [], "status aguardando_cliente: lembrete do que falta"
    else:
        tabela = {
            "atraso_entrega": ("acionar_transportadora", ["contatar_cliente"], "fora do SLA, até 10 dias úteis: acionar a transportadora"),
            "rastreio_parado": ("acionar_transportadora", [], "rastreio parado: acionar a transportadora"),
            "extravio": ("reenviar", ["acionar_transportadora"], "extravio: reenviar"),
            "devolvido_transportadora": ("reenviar", ["contatar_cliente"], "devolvido: reenviar confirmando o endereço"),
            "avaria_transporte": ("reenviar", [], "avaria: reenvio sem custo, mediante foto (S9)"),
            "vazamento_produto": ("reenviar", [], "vazamento: reenvio sem custo, mediante foto (S9)"),
            "item_faltante": ("reenviar", [], "item faltante: reenvio sem custo, mediante foto (S9)"),
            "falha_personalizacao": ("refazer_personalizacao", [], "falha de personalização: nova produção, mediante foto (S9)"),
            "pagamento_pendente": ("contatar_cliente", [], "pagamento pendente: contatar o cliente"),
            "endereco_divergente": ("contatar_cliente", [], "endereço divergente: confirmar com o cliente"),
            "ruptura_pos_venda": ("contatar_cliente", ["reembolsar"], "ruptura: oferecer espera ou reembolso"),
        }
        a, ac, rac = tabela[tipo]
    # H2b depende da ação: reenvio padrão com custo acima do limite vai para a analista.
    if a in ("reenviar", "refazer_personalizacao"):
        from src.agente.esquemas import Decisao
        r = regra_humano(f, Decisao(acao=a, justificativa="checagem do custo do reenvio",
                                    mensagem_cliente="Mande uma foto do produto.", confianca="alta", precisa_humano=False))
        if r and r[0] == "H2b":
            return dict(acao_esperada="escalar_humano", acoes_aceitaveis=["escalar_humano"], deve_ir_para_humano=True,
                        motivo_humano_esperado="H2b", racional=f"SPEC.md, regra H2b: {r[1]}")
    return dict(acao_esperada=a, acoes_aceitaveis=sorted({a, *ac}), deve_ir_para_humano=False,
                motivo_humano_esperado=None, racional=f"SPEC.md, política de ações: {rac}")


def _sem_decisao():
    """Regras H1–H5 não dependem da decisão do modelo; H2/H3 (reembolso) são checadas no eval."""
    from src.agente.esquemas import Decisao
    return Decisao(acao="aguardar", justificativa="placeholder para checar regras de dados",
                   confianca="alta", precisa_humano=False)


def sortear() -> list[str]:
    df = base_trabalho()
    _, exemplos, _ = carregar_prompt("decisao")
    df = df[~df["order_id"].isin(exemplos)]
    escolhidos: list[str] = []

    def pega(sub: pd.DataFrame, n: int):
        sub = sub[~sub["order_id"].isin(escolhidos)]
        escolhidos.extend(sub.sample(min(n, len(sub)), random_state=SEMENTE)["order_id"].tolist())

    for tipo in sorted(df["tipo_excecao"].unique()):
        pega(df[df["tipo_excecao"] == tipo], 2)
    atraso = df["tipo_excecao"] == "atraso_entrega"
    pega(df[atraso & ~df["entregue"] & (df["atraso_du_sla"] == 0)], 2)          # dentro do SLA
    pega(df[atraso & ~df["entregue"] & (df["atraso_du_prometido"] > 10)], 2)    # H4
    pega(df[atraso & df["entregue"]], 1)                                         # atraso já entregue
    pega(df[df["status_incoerente"]], 2)                                         # H1
    pega(df[df["cliente_alto_valor"] & (df["tipo_excecao"] == "ruptura_pos_venda")], 1)
    pega(df[df["status"] == "aguardando_cliente"], 2)
    pega(df[df["status_em_conflito"]], 1)                                        # duplicata
    return escolhidos


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if ARQ.exists() and any('"anotado_por": "levi' in l or "revisado" in l for l in ARQ.read_text(encoding="utf-8").splitlines()):
        raise SystemExit("gabarito já tem linhas revisadas; não sobrescrevo")
    linhas = []
    for o in sortear():
        f = montar_ficha(o)
        rot = rotular(f)
        pad = f["padrao_causa_raiz"]
        linhas.append({"order_id": o, "tipo_excecao": f["excecao"]["tipo"], **rot,
                       "padrao_esperado": pad["id"] if pad else None, "anotado_por": "claude_pendente_levi"})
    ARQ.write_text("\n".join(json.dumps(l, ensure_ascii=False) for l in linhas) + "\n", encoding="utf-8")
    print(f"{len(linhas)} casos em {ARQ.relative_to(RAIZ)}")
    print(pd.Series([l["acao_esperada"] for l in linhas]).value_counts().to_string())
    print("vão para humano:", sum(l["deve_ir_para_humano"] for l in linhas))
    print("com padrão:", sum(l["padrao_esperado"] is not None for l in linhas))


if __name__ == "__main__":
    main()
