"""Reaplica as regras de humano no loop às decisões gravadas em demo/cache/, sem chamar o modelo.

Uso: python -m src.agente.reaplicar   (depois de mudar src/agente/regras.py)
"""

import sys
from collections import Counter

from src.agente.esquemas import Resultado
from src.agente.pipeline import PASTA_CACHE, carregar_prompt, reaplicar_regras


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    versao, _, _ = carregar_prompt("decisao")
    mudou = Counter()
    for arq in sorted(PASTA_CACHE.glob(f"G*_v{versao}.json")):
        antigo = Resultado.model_validate_json(arq.read_text(encoding="utf-8"))
        novo = reaplicar_regras(antigo)
        if (antigo.regra_aplicada, antigo.acao_final) != (novo.regra_aplicada, novo.acao_final):
            mudou[f"{antigo.regra_aplicada or 'auto'} → {novo.regra_aplicada or 'auto'}"] += 1
            print(f"{novo.order_id} {novo.tipo_excecao}: {antigo.acao_final.value} → {novo.acao_final.value} ({novo.regra_aplicada}: {novo.motivo_humano})")
        arq.write_text(novo.model_dump_json(indent=1), encoding="utf-8")
    print("\nmudanças:", dict(mudou) or "nenhuma")


if __name__ == "__main__":
    main()
