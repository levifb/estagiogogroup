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


def evidencias() -> list[dict]:
    """Evidência de cada padrão, toda calculada pelo código (src/dados/padroes.py)."""
    df = base_trabalho()
    out = []
    for p in padroes():
        semanas = {k.split("/")[0]: v for k, v in p.semanas.items()}
        out.append({
            "padrao_id": p.id, "dono": DONOS.get(p.dimensao, "Operações"),
            "evidencia": {
                "grupo": f"{_DESCRICAO_DIM.get(p.dimensao, p.dimensao)}: {p.valor}",
                "tipos_de_excecao": p.tipos, "excecoes_do_padrao": p.casos, "excecoes_no_grupo": p.exc_no_grupo,
                "proporcao_no_grupo": round(p.taxa_grupo, 3), "proporcao_nos_demais": round(p.taxa_base, 3),
                "vezes_acima_da_base": round(p.razao, 1), "excecoes_acima_do_esperado": round(p.excesso),
                "valor_pago_dos_pedidos": round(p.valor_total, 2),
                "excecoes_por_semana_do_pedido": semanas,
            },
        })
    atraso = df[df["tipo_excecao"] == "atraso_entrega"]
    out.append({
        "padrao_id": "P00", "dono": "TI do checkout",
        "evidencia": {
            "grupo": "cálculo da data prometida no checkout",
            "regra_do_parametro": "1 dia útil de separação + SLA da transportadora, em dias úteis",
            "como_o_sistema_calcula": "data do pedido + 1 + SLA em dias corridos (bate em 100% das exceções)",
            "atrasos_registrados": int(len(atraso)),
            "atrasos_dentro_do_sla_contratado": int((atraso["atraso_du_sla"] == 0).sum()),
            "mediana_de_dias_que_a_promessa_antecipa": int((df["prazo_correto"] - df["data_prometida"]).dt.days.median()),
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
