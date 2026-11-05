"""Processa a fila do dia (150 casos) ao vivo e grava o cache do modo demo.

Respeita o limite gratuito do Groq: casos já em cache (mesma versão do prompt) são pulados,
então dá para interromper e retomar.

Uso: python -m src.agente.lote [--dia 0] [--limite N]
"""

import argparse
import sys
import time

from src.agente.ficha import fila_do_dia, montar_ficha
from src.agente.pipeline import carregar_prompt, ler_cache, processar


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--dia", type=int, default=0)
    ap.add_argument("--limite", type=int, default=None)
    args = ap.parse_args()
    versao, _, _ = carregar_prompt("decisao")
    fila = fila_do_dia(args.dia)[: args.limite]
    t0, feitos, falhas = time.time(), 0, 0
    for i, o in enumerate(fila, 1):
        tipo = montar_ficha(o)["excecao"]["tipo"]
        if ler_cache(o, tipo, versao) is not None:
            continue
        r = processar(o, modo="ao_vivo")
        feitos += 1
        falhas += r.fonte != "ao_vivo"
        print(f"[{i:3}/{len(fila)}] {o} {tipo:25} → {r.acao_final.value:22} humano={r.vai_para_humano} {r.fonte} {r.erro or ''}", flush=True)
    print(f"\n{feitos} processados, {falhas} sem resposta do modelo, {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
