"""Registro de números: cada script de análise devolve uma lista de Numero.

`python -m analises.gerar_numeros` roda todos os scripts e reescreve
docs/NUMEROS.md (para pessoas) e docs/numeros.json (para a API e a interface).
"""

from dataclasses import asdict, dataclass


@dataclass
class Numero:
    id: str
    valor: float
    texto: str        # valor formatado para exibição, ex.: "2.000" ou "R$ 13.570"
    definicao: str    # definição exata, com a conta quando for derivado
    script: str
    estimativa: bool = False

    def dict(self):
        return asdict(self)


def br_int(x: float) -> str:
    return f"{x:,.0f}".replace(",", ".")


def br_reais(x: float) -> str:
    return "R$ " + br_int(x)


def br_pct(x: float, casas: int = 0) -> str:
    return f"{100 * x:.{casas}f}%".replace(".", ",")


def imprimir(numeros: list[Numero]) -> None:
    for n in numeros:
        marca = " (estimativa)" if n.estimativa else ""
        print(f"{n.id:5} {n.texto:>14}  {n.definicao}{marca}")
