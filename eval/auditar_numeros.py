"""Confere se cada número citado com id ("R$ 18.175 [N72]") bate com docs/numeros.json.

Uso: python -m eval.auditar_numeros   (sai com código 1 se achar divergência)
"""

import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ARQUIVOS = ["README.md", "SPEC.md"]
# A interface lê os números de web/public/data/numeros.json pelo id; o auditor confere que essa cópia
# é idêntica ao registro e que todo id citado em web/src existe.
# "valor [Nxx]": pega o trecho numérico (ou data) logo antes do colchete. Citação com vários ids
# ("[N44, N50]") é referência de evidência, não afirmação de um valor, e não é conferida aqui.
CITACAO = re.compile(r"((?:R\$\s?)?\d[\d\.,/]*\s?(?:%|h|dias)?)\**\s*\[(N\d{2,3})\]")


def normalizar(t: str) -> str:
    return t.replace(" ", "").replace("dias", "").replace(" ", "")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    numeros = json.loads((RAIZ / "docs" / "numeros.json").read_text(encoding="utf-8"))["numeros"]
    problemas, conferidos = [], 0
    for nome in ARQUIVOS:
        texto = (RAIZ / nome).read_text(encoding="utf-8")
        for valor, nid in CITACAO.findall(texto):
            conferidos += 1
            if nid not in numeros:
                problemas.append(f"{nome}: {nid} não existe em docs/NUMEROS.md")
            elif normalizar(valor) != normalizar(numeros[nid]["texto"]):
                problemas.append(f"{nome}: '{valor.strip()}' [{nid}] difere do registro '{numeros[nid]['texto']}'")
        for nid in set(re.findall(r"\[(N\d{2,3})\b", texto)) - set(numeros):
            problemas.append(f"{nome}: {nid} citado mas inexistente")
    web = RAIZ / "web" / "public" / "data" / "numeros.json"
    if not web.exists() or json.loads(web.read_text(encoding="utf-8"))["numeros"] != numeros:
        problemas.append("web/public/data/numeros.json difere de docs/numeros.json (rode python -m src.exportar)")
    for arq in (RAIZ / "web" / "src").glob("*.tsx"):
        for nid in set(re.findall(r'id="(N\d{2,3})"', arq.read_text(encoding="utf-8"))) - set(numeros):
            problemas.append(f"{arq.name}: {nid} citado mas inexistente")
    print(f"{conferidos} citações conferidas em {', '.join(ARQUIVOS)}; interface conferida contra o registro")
    for p in problemas:
        print("DIVERGE", p)
    print("ok" if not problemas else f"{len(problemas)} problemas")
    return 1 if problemas else 0


if __name__ == "__main__":
    raise SystemExit(main())
