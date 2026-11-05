"""Ficha do caso: tudo o que o agente sempre precisa, calculado pelo código.

O modelo interpreta a ficha; ele não calcula dias úteis, valores nem probabilidades.
"""

from functools import lru_cache

import pandas as pd

from src.dados.fonte import DATA_REFERENCIA
from src.dados.padroes import detectar
from src.negocio.risco import ACAO_PADRAO, CMV, CasoRisco, custo_acao, custo_de_espera, perda_esperada
from src.negocio.simulacao import casos_e_base, simular

DONOS = {
    "transportadora": "Gestão de transportadoras",
    "transportadora+regiao": "Gestão de transportadoras",
    "transportadora+uf": "Gestão de transportadoras",
    "cd": "Supervisão do CD", "turno": "Supervisão do CD", "cd+turno": "Supervisão do CD",
    "maquina": "Manutenção",
    "lote": "Qualidade / fornecedor", "sku+lote": "Qualidade / fornecedor", "sku": "Qualidade / fornecedor",
    "marca": "Compras / planejamento",
    "brinde": "Supervisão do CD",
}


@lru_cache(maxsize=1)
def _indices():
    casos, df = casos_e_base()
    padroes = detectar(df)
    por_pedido = {o: p for p in padroes for o in p.order_ids}
    dia_plano = dict(zip(df["order_id"], simular()["otimizado"].dia))
    return {c.order_id: c for c in casos}, df.set_index("order_id"), padroes, por_pedido, dia_plano


def padroes():
    return _indices()[2]


def plano() -> pd.DataFrame:
    """Plano otimizado: order_id, dia (0 = 30/09/2026), perda hoje e custo de esperar 1 dia útil."""
    casos, df, _, _, dia = _indices()
    linhas = [{"order_id": o, "dia": int(dia[o]), "perda_hoje": perda_esperada(c, 0)["total"],
               "custo_espera_1d": custo_de_espera(c, 0, 1)} for o, c in casos.items()]
    return pd.DataFrame(linhas).sort_values(["dia", "custo_espera_1d", "perda_hoje"], ascending=[True, False, False])


def fila_do_dia(dia: int = 0) -> list[str]:
    p = plano()
    return p[p["dia"] == dia]["order_id"].tolist()


def _d(x):
    return None if pd.isna(x) else pd.Timestamp(x).strftime("%d/%m/%Y")


def montar_ficha(order_id: str) -> dict:
    casos, df, _, por_pedido, dia = _indices()
    if order_id not in casos:
        raise KeyError(f"pedido {order_id} não está entre as exceções abertas")
    c: CasoRisco = casos[order_id]
    r = df.loc[order_id]
    p0, p5 = perda_esperada(c, 0), perda_esperada(c, 5)
    pad = por_pedido.get(order_id)
    custos = {
        "reenviar": round(CMV * c.valor + c.frete, 2),
        "refazer_personalizacao": round(CMV * c.valor + c.frete, 2),
        "reembolsar": round(c.valor, 2),
        "acao_padrao_do_tipo": ACAO_PADRAO[c.tipo],
        "custo_acao_padrao": round(custo_acao(c.tipo, c.valor, c.frete), 2),
    }
    dias_recebimento = None
    if r["entregue"]:
        dias_recebimento = int((r["data_abertura_excecao"] - r["data_entrega"]).days)
    return {
        "data_referencia": DATA_REFERENCIA.strftime("%d/%m/%Y"),
        "pedido": {
            "order_id": order_id, "marca": r["marca"], "produto": r["descricao_produto"], "sku": r["sku"],
            "valor_pago": round(float(r["valor"]), 2), "qtd_itens": int(r["qtd_itens"]),
            "brinde_no_pedido": bool(r["brinde_no_pedido"]), "data_pedido": _d(r["data_pedido"]),
            "cd": r["cd"], "turno": r["turno"], "maquina": None if pd.isna(r["maquina"]) else r["maquina"],
            "lote_produto": r["lote_produto"],
        },
        "excecao": {
            "tipo": r["tipo_excecao"], "status": r["status"], "aberta_em": _d(r["data_abertura_excecao"]),
            "dias_aberta": int(r["idade_dias"]),
            "status_incoerente_com_tipo": bool(r["status_incoerente"]),
            "registro_duplicado_com_status_diferente": bool(r["status_em_conflito"]),
        },
        "entrega": {
            "transportadora": r["transportadora"], "uf": r["uf"], "cidade": r["cidade"],
            "sla_contratado_dias_uteis": int(r["sla_contratado_dias_uteis"]),
            "data_prometida_ao_cliente": _d(r["data_prometida"]),
            "prazo_correto_pelo_sla_dias_uteis": _d(r["prazo_correto"]),
            "entregue": bool(r["entregue"]), "data_entrega": _d(r["data_entrega"]),
            "dias_uteis_atraso_vs_prometido": int(r["atraso_du_prometido"]),
            "dias_uteis_atraso_vs_sla_contratado": int(r["atraso_du_sla"]),
            "dentro_do_sla_contratado": bool(r["atraso_du_sla"] == 0),
            "dias_entre_recebimento_e_reclamacao": dias_recebimento,
        },
        "cliente": {
            "customer_id": r["customer_id"], "n_pedidos": int(r["n_pedidos"]),
            "receita_acumulada": round(float(r["receita_acumulada"]), 2),
            "alto_valor_acima_1500": bool(r["cliente_alto_valor"]),
            "contatos_atendimento_12m": int(r["n_contatos_atendimento"]),
        },
        "risco": {
            "prob_cancelamento_hoje": p0["p_cancelamento"],
            "prob_cancelamento_em_5_dias_uteis": p5["p_cancelamento"],
            "perda_esperada_hoje": round(p0["total"], 2),
            "custo_de_esperar_1_dia_util": round(custo_de_espera(c, 0, 1), 2),
            "dia_no_plano_otimizado": int(dia[order_id]),
        },
        "custos_acoes": custos,
        "padrao_causa_raiz": None if pad is None else {
            "id": pad.id, "descricao": f"{pad.dimensao} = {pad.valor} ({', '.join(pad.tipos)})",
            "casos": pad.casos, "dono": DONOS.get(pad.dimensao, "Operações"),
        },
    }
