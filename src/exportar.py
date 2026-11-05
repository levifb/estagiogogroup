"""Exporta tudo o que a interface mostra para JSON estático, e os dados da função ao vivo.

- web/public/data/: lido pelo front (fila, casos, chamados, simulação, números, eval).
- api/_dados/: lido pela função publicada (fichas da fila e respostas pré-calculadas das ferramentas).

Assim a versão publicada não precisa de pandas nem scipy, e a tela funciona sem o Groq.
Uso: python -m src.exportar
"""

import json
import shutil
import sys
from pathlib import Path

from src.agente import ferramentas
from src.agente.ficha import fila_do_dia, montar_ficha, plano
from src.agente.investigador import chamados_em_cache, evidencias
from src.agente.pipeline import carregar_prompt, decidir
from src.negocio.simulacao import simular

RAIZ = Path(__file__).resolve().parents[1]
WEB = RAIZ / "web" / "public" / "data"
API = RAIZ / "api" / "_dados"


def _pendente(r) -> bool:
    return r.fonte == "sem_modelo" and r.regra_aplicada == "H6"


def _grava(caminho: Path, obj) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":"), default=str), encoding="utf-8")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    versao, _, _ = carregar_prompt("decisao")
    # Sobrescreve em vez de apagar a pasta (o OneDrive pode travar a pasta); remove só casos que saíram da fila.
    (WEB / "casos").mkdir(parents=True, exist_ok=True)

    p = plano().reset_index(drop=True)
    p["prioridade"] = range(1, len(p) + 1)
    hoje = fila_do_dia(0)
    fichas, fila = {}, []
    for o in hoje:
        f = montar_ficha(o)
        fichas[o] = f
        r = decidir(f, modo="demo")
        linha = p[p["order_id"] == o].iloc[0]
        fila.append({
            "order_id": o, "prioridade": int(linha["prioridade"]), "tipo": f["excecao"]["tipo"],
            "status": f["excecao"]["status"], "marca": f["pedido"]["marca"], "valor": f["pedido"]["valor_pago"],
            "perda_hoje": round(float(linha["perda_hoje"]), 2), "custo_espera_1d": round(float(linha["custo_espera_1d"]), 2),
            "padrao": (f["padrao_causa_raiz"] or {}).get("id"),
            # Sem decisão do modelo e sem regra de dados (H1–H5): o caso ainda não foi processado.
            "acao": r.acao_final.value, "humano": r.vai_para_humano and not _pendente(r),
            "pendente": _pendente(r), "motivo_humano": r.motivo_humano,
            "regra": r.regra_aplicada, "fonte": r.fonte,
        })
        _grava(WEB / "casos" / f"{o}.json", r.model_dump(mode="json"))
    for antigo in (WEB / "casos").glob("*.json"):
        if antigo.stem not in fichas:
            antigo.unlink(missing_ok=True)

    sim = simular()
    _grava(WEB / "fila.json", {"data_referencia": "30/09/2026", "versao_prompt": versao, "casos": fila})
    _grava(WEB / "simulacao.json", {k: {"perda_total": round(v.perda_total, 2),
                                        "perda_por_dia": [round(x, 2) for x in v.perda_por_dia]} for k, v in sim.items()})
    chamados = {c.padrao_id: c.model_dump(mode="json") for c in chamados_em_cache()}
    _grava(WEB / "chamados.json", [chamados.get(ev["padrao_id"], {"padrao_id": ev["padrao_id"], "dono": ev["dono"],
                                                                  "evidencia": ev["evidencia"], "pendente": True})
                                   for ev in evidencias()])
    shutil.copy(RAIZ / "docs" / "numeros.json", WEB / "numeros.json")
    resultados = sorted((RAIZ / "eval" / "resultados").glob("*_v*.json"))
    # Eval principal: o do modelo padrão (arquivos de outros modelos levam o nome do modelo no fim, ex.: _gpt-oss-20b).
    vivos = [r for r in resultados if "_demo" not in r.name and r.stem.split("_")[-1].startswith("v")]
    if vivos:
        ult = json.loads(vivos[-1].read_text(encoding="utf-8"))
        _grava(WEB / "eval.json", {"arquivo": vivos[-1].name, "versao_prompt": ult["versao_prompt"],
                                   "modelo": ult["modelo"], "resumo": ult["resumo"]})

    _grava(API / "fichas.json", fichas)
    _grava(API / "ferramentas.json", ferramentas.precalcular(hoje, [f["cliente"]["customer_id"] for f in fichas.values()]))

    em_cache = sum(not c["pendente"] for c in fila)
    print(f"fila: {len(fila)} casos ({em_cache} com decisão em cache); chamados: {len(chamados)}; arquivos em {WEB.relative_to(RAIZ)} e {API.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
