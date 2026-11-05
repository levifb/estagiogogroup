"""Avalia o agente contra o gabarito, etapa por etapa, e compara com uma linha de base sem LLM.

Uso, a partir da raiz:
  python -m eval.eval            # chama o modelo ao vivo e grava o cache do modo demo
  python -m eval.eval --demo     # usa só o cache (sem rede)
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from eval.mensagens import checar  # noqa: E402
from src.agente.ficha import montar_ficha  # noqa: E402
from src.agente.llm import modelo  # noqa: E402
from src.agente.pipeline import carregar_prompt, processar  # noqa: E402
from src.agente.regras import regra_humano  # noqa: E402
from src.negocio.risco import ACAO_PADRAO  # noqa: E402


def linha_de_base(g: dict) -> tuple[str, bool]:
    """Automação simples, sem LLM: ação fixa por tipo + as mesmas regras de dados H1–H5."""
    f = montar_ficha(g["order_id"])
    r = regra_humano(f, _decisao_fixa(ACAO_PADRAO[g["tipo_excecao"]]))
    if r and r[0] != "H6":
        return "escalar_humano", True
    return ACAO_PADRAO[g["tipo_excecao"]], False


def _decisao_fixa(acao: str):
    from src.agente.esquemas import Decisao
    return Decisao(acao=acao, justificativa="linha de base sem LLM", mensagem_cliente="(sem mensagem)",
                   confianca="alta", precisa_humano=False)


def pct(a, b):
    return f"{a}/{b} ({100 * a / b:.0f}%)" if b else "n/a"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--limite", type=int, default=None)
    ap.add_argument("--sem-gravar", action="store_true", help="não grava o cache (para avaliar outro modelo sem sobrescrever)")
    args = ap.parse_args()

    gab = [json.loads(l) for l in (RAIZ / "eval" / "gabarito.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    gab = gab[: args.limite] if args.limite else gab
    versao, exemplos, _ = carregar_prompt("decisao")
    sobrepostos = {g["order_id"] for g in gab} & set(exemplos)
    if sobrepostos:
        raise SystemExit(f"exemplos do prompt dentro do gabarito: {sobrepostos}")

    linhas, t0 = [], time.time()
    for i, g in enumerate(gab, 1):
        r = processar(g["order_id"], modo="demo" if args.demo else "ao_vivo", gravar=not args.sem_gravar)
        d = r.decisao_modelo
        base_acao, base_humano = linha_de_base(g)
        tokens = sum(x.get("tokens") or 0 for x in r.rastro if x.get("etapa", "").startswith("modelo"))
        linhas.append({
            "order_id": g["order_id"], "tipo": g["tipo_excecao"], "fonte": r.fonte,
            "esperado": g["acao_esperada"], "aceitaveis": g["acoes_aceitaveis"], "obtido": r.acao_final.value,
            "proposta_modelo": d.acao.value if d else None,
            "humano_esperado": g["deve_ir_para_humano"], "humano_obtido": r.vai_para_humano,
            "regra": r.regra_aplicada, "motivo_humano": r.motivo_humano,
            "padrao_esperado": g["padrao_esperado"], "padrao_obtido": d.pertence_a_padrao if d else None,
            "json_1a": any(x.get("etapa") == "json_valido" and x.get("tentativa") == 1 for x in r.rastro),
            "ferramentas": [x["nome"] for x in r.rastro if x.get("etapa") == "ferramenta"],
            "tokens": tokens, "justificativa": d.justificativa if d else r.erro,
            "mensagem": d.mensagem_cliente if d else None,
            "msg_falhas": checar(r.ficha, d.acao.value, d.mensagem_cliente) if d else [],
            "base_acao": base_acao, "base_humano": base_humano,
        })
        print(f"[{i:2}/{len(gab)}] {g['order_id']} {g['tipo_excecao']:25} esperado={g['acao_esperada']:22} obtido={r.acao_final.value:22} {r.fonte}", flush=True)

    n = len(linhas)
    exata = sum(l["obtido"] == l["esperado"] for l in linhas)
    aceit = sum(l["obtido"] in l["aceitaveis"] for l in linhas)
    base_ok = sum(l["base_acao"] in l["aceitaveis"] for l in linhas)
    deve = [l for l in linhas if l["humano_esperado"]]
    foi = [l for l in linhas if l["humano_obtido"]]
    vp = sum(l["humano_esperado"] and l["humano_obtido"] for l in linhas)
    com_pad = [l for l in linhas if l["padrao_esperado"]]
    pad_ok = sum(l["padrao_obtido"] == l["padrao_esperado"] for l in com_pad)
    sem_pad = [l for l in linhas if not l["padrao_esperado"]]
    pad_falso = sum(l["padrao_obtido"] is not None for l in sem_pad)
    json1 = sum(l["json_1a"] for l in linhas if l["fonte"] == "ao_vivo")
    vivos = sum(l["fonte"] == "ao_vivo" for l in linhas)
    auto = sum(not l["humano_obtido"] for l in linhas)
    tok = [l["tokens"] for l in linhas if l["tokens"]]
    com_msg = [l for l in linhas if l["proposta_modelo"] not in (None, "aguardar", "escalar_humano")]
    msg_ok = sum(not l["msg_falhas"] for l in com_msg)
    from collections import Counter
    falhas_msg = Counter(f for l in linhas for f in l["msg_falhas"])

    resumo = {
        "acao_exata": exata, "acao_aceitavel": aceit, "linha_de_base_aceitavel": base_ok, "n": n,
        "recall_humano": [vp, len(deve)], "precisao_humano": [vp, len(foi)],
        "padrao_certo": [pad_ok, len(com_pad)], "padrao_falso": [pad_falso, len(sem_pad)],
        "json_1a_tentativa": [json1, vivos], "resolvidos_sozinhos": [auto, n],
        "tokens_medio": round(sum(tok) / len(tok)) if tok else None,
        "mensagens_sem_problema": [msg_ok, len(com_msg)], "falhas_mensagem": dict(falhas_msg),
        "segundos_total": round(time.time() - t0, 1),
    }
    print("\n=== RESUMO", f"(prompt v{versao}, modelo {modelo()}, {'cache' if args.demo else 'ao vivo'})")
    print(f"RECALL 'deve ir para humano':  {pct(vp, len(deve))}   <- erro caro: caso de risco tratado sozinho")
    print(f"Precisão do envio ao humano:   {pct(vp, len(foi))}")
    print(f"Ação final aceitável:          {pct(aceit, n)}   (exata: {pct(exata, n)})")
    print(f"Linha de base sem LLM:         {pct(base_ok, n)}")
    print(f"Padrão de causa raiz certo:    {pct(pad_ok, len(com_pad))}   padrão inventado: {pct(pad_falso, len(sem_pad))}")
    print(f"JSON válido na 1ª tentativa:   {pct(json1, vivos)}")
    print(f"Mensagens sem problema:        {pct(msg_ok, len(com_msg))}   {dict(falhas_msg) or ''}")
    print(f"Resolvidos sem humano:         {pct(auto, n)}   tokens/caso: {resumo['tokens_medio']}")

    erros = [l for l in linhas if l["obtido"] not in l["aceitaveis"] or l["humano_obtido"] != l["humano_esperado"]
             or (l["padrao_esperado"] or None) != (l["padrao_obtido"] or None) or l["msg_falhas"]]
    if erros:
        print("\n=== ERROS")
        for l in erros:
            print(f"- {l['order_id']} {l['tipo']}: esperado {l['esperado']} (humano={l['humano_esperado']}, padrão={l['padrao_esperado']}) "
                  f"| obtido {l['obtido']} (proposta {l['proposta_modelo']}, humano={l['humano_obtido']} {l['regra'] or ''}, padrão={l['padrao_obtido']})")
            print(f"    {(l['justificativa'] or '')[:260]}")
            if l["msg_falhas"]:
                print(f"    mensagem {l['msg_falhas']}: {(l['mensagem'] or '')[:300]}")

    pasta = RAIZ / "eval" / "resultados"
    pasta.mkdir(parents=True, exist_ok=True)
    sufixo_modelo = "" if modelo() == "openai/gpt-oss-120b" else "_" + modelo().split("/")[-1]
    nome = f"{datetime.now():%Y-%m-%d_%H%M}_v{versao}{sufixo_modelo}{'_demo' if args.demo else ''}.json"
    (pasta / nome).write_text(json.dumps({"versao_prompt": versao, "modelo": modelo(), "resumo": resumo, "casos": linhas},
                                         ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nsalvo em eval/resultados/{nome}")


if __name__ == "__main__":
    main()
