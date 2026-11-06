"""Investigador de causa raiz: o código detecta e mede, o modelo redige o chamado.

Uso: python -m src.agente.investigador   (gera os chamados ao vivo e grava em demo/cache/)
"""

import json
import sys
from pathlib import Path

from src.agente import llm
from src.agente.esquemas import Chamado, ChamadoTexto
from src.agente.ficha import DONOS, padroes
from src.agente.pipeline import PASTA_CACHE, carregar_prompt
from src.dados.base import base_trabalho

_DESCRICAO_DIM = {
    "transportadora+regiao": "transportadora e região de destino", "cd+turno": "CD e turno de separação",
    "transportadora": "transportadora", "sku+lote": "SKU e lote de fabricação", "maquina": "máquina de impressão",
    "marca": "marca",
}


def _pct(x: float) -> str:
    return f"{100 * x:.0f}%"


def _reais(v: float) -> str:
    return "R$ " + f"{v:,.0f}".replace(",", ".")


def evidencias() -> list[dict]:
    """Evidência de cada padrão, toda calculada pelo código (src/dados/padroes.py)."""
    df = base_trabalho()
    out = []
    for p in padroes():
        semanas = {k.split("/")[0]: v for k, v in p.semanas.items()}
        linhas = df[df["order_id"].isin(p.order_ids)]
        ev = {
            "grupo": f"{_DESCRICAO_DIM.get(p.dimensao, p.dimensao)}: {p.valor}",
            "tipos de exceção": ", ".join(p.tipos),
            "exceções deste tipo no grupo": f"{p.casos} de {p.exc_no_grupo} exceções do grupo ({_pct(p.taxa_grupo)})",
            "mesma proporção nos demais grupos": _pct(p.taxa_base),
            "vezes acima dos demais": f"{p.razao:.1f}".replace(".", ","),
            "exceções além do esperado": str(round(p.excesso)),
            "valor pago dos pedidos afetados": _reais(p.valor_total),
            "exceções por semana do pedido": semanas,
        }
        # Evidência específica de cada tipo de padrão: é o que aponta a causa provável.
        if p.dimensao in ("cd", "turno", "cd+turno") and "item_faltante" in p.tipos:
            ev["pedidos com brinde entre os itens faltantes do grupo"] = _pct(linhas["brinde_no_pedido"].mean())
            ev["pedidos com brinde entre todas as exceções"] = _pct(df["brinde_no_pedido"].mean())
        if p.dimensao.startswith("transportadora"):
            ent = df[df["entregue"]]
            grupo = ent[ent["order_id"].isin(p.order_ids)]
            if len(grupo):
                ev["dias úteis médios além do SLA nas entregas do grupo"] = f"{grupo['atraso_du_sla'].mean():.1f}".replace(".", ",")
                ev["dias úteis médios além do SLA nas demais entregas"] = f"{ent[~ent['order_id'].isin(p.order_ids)]['atraso_du_sla'].mean():.1f}".replace(".", ",")
        out.append({"padrao_id": p.id, "dono": DONOS.get(p.dimensao, "Operações"), "evidencia": ev})
    atraso = df[df["tipo_excecao"] == "atraso_entrega"]
    out.append({
        "padrao_id": "P00", "dono": "TI do checkout",
        "evidencia": {
            "grupo": "cálculo da data prometida no checkout",
            "regra combinada com as transportadoras": "1 dia útil de separação + SLA da transportadora, em dias úteis",
            "como o sistema calcula hoje": "data do pedido + 1 + SLA em dias corridos (bate em 100% das exceções)",
            "total de exceções de atraso (por todas as causas)": str(int(len(atraso))),
            "atrasos causados por esta regra (dentro do SLA contratado, só passaram da data prometida)": str(int((atraso["atraso_du_sla"] == 0).sum())),
            "quantos dias antes do prazo correto a promessa cai (mediana, dias corridos)": str(int((df["prazo_correto"] - df["data_prometida"]).dt.days.median())),
        },
    })
    return out


def _arquivo(pid: str, versao: int) -> Path:
    return PASTA_CACHE / f"chamado_{pid}_v{versao}.json"


def gerar_chamado(ev: dict) -> tuple[Chamado | None, list]:
    versao, _, sistema = carregar_prompt("chamado")
    msgs = [{"role": "system", "content": sistema},
            {"role": "user", "content": f"<dono>{ev['dono']}</dono>\n<evidencia>\n"
                                        f"{json.dumps(ev['evidencia'], ensure_ascii=False)}\n</evidencia>"}]
    texto, rastro = llm.gerar(msgs, ChamadoTexto)
    if texto is None:
        return None, rastro
    return Chamado(**texto.model_dump(), padrao_id=ev["padrao_id"], dono=ev["dono"], evidencia=ev["evidencia"]), rastro


def chamados_em_cache() -> list[Chamado]:
    versao, _, _ = carregar_prompt("chamado")
    out = []
    for ev in evidencias():
        arq = _arquivo(ev["padrao_id"], versao)
        if arq.exists():
            out.append(Chamado.model_validate_json(arq.read_text(encoding="utf-8")))
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    versao, _, _ = carregar_prompt("chamado")
    PASTA_CACHE.mkdir(parents=True, exist_ok=True)
    for ev in evidencias():
        c, rastro = gerar_chamado(ev)
        if c is None:
            print(ev["padrao_id"], "FALHOU", rastro[-1])
            continue
        _arquivo(ev["padrao_id"], versao).write_text(c.model_dump_json(indent=1), encoding="utf-8")
        print(f"{c.padrao_id} [{c.dono}] {c.titulo}")


if __name__ == "__main__":
    main()
