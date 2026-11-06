"""Roda todas as análises e reescreve docs/NUMEROS.md e docs/numeros.json.

Uso, a partir da raiz: python -m analises.gerar_numeros
"""

import importlib
import json
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

MODULOS = ["a01_perfil", "a02_prazo_prometido", "a03_padroes", "a04_valor_em_risco", "a05_simulacao", "a06_fila_do_dia"]


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    numeros = []
    for nome in MODULOS:
        try:
            mod = importlib.import_module(f"analises.{nome}")
        except ModuleNotFoundError as e:
            if e.name == f"analises.{nome}":
                print(f"(ainda não existe: {nome})")
                continue
            raise
        numeros += mod.calcular()

    ids = [n.id for n in numeros]
    repetidos = {i for i in ids if ids.count(i) > 1}
    if repetidos:
        raise SystemExit(f"ids repetidos: {sorted(repetidos)}")

    hoje = date.today().isoformat()
    linhas = [
        "# Números do projeto",
        "",
        "Gerado por `python -m analises.gerar_numeros`. Não edite à mão: mude o script e rode de novo.",
        "Todo número que aparece no README, na interface ou no LOG é citado pelo id desta tabela.",
        "",
        "| id | número | definição | script | gerado em |",
        "|---|---|---|---|---|",
    ]
    for n in numeros:
        d = n.definicao + (" **(estimativa)**" if n.estimativa else "")
        linhas.append(f"| {n.id} | {n.texto} | {d.replace('|', '/')} | `{n.script}` | {hoje} |")
    (RAIZ / "docs" / "NUMEROS.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    payload = {"gerado_em": hoje, "numeros": {n.id: n.dict() for n in numeros}}
    (RAIZ / "docs" / "numeros.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(numeros)} números gravados em docs/NUMEROS.md e docs/numeros.json")


if __name__ == "__main__":
    main()
