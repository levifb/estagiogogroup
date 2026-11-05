"""Perda esperada de uma exceção conforme o dia em que ela é tratada.

Fontes: dados/operacoes/parametros.md (tabela de cancelamento, CMV, frete, reembolso,
recompra) e as suposições S1 a S6 do SPEC.md. Nada aqui chama LLM.
"""

from dataclasses import dataclass

import pandas as pd

from src.dados import calendario
from src.dados.fonte import DATA_REFERENCIA

CMV = 0.24                    # parametros.md: custo da mercadoria, % do valor
P_RECOMPRA_ALTO_VALOR = 0.70  # receita acumulada > R$ 1.500
P_RECOMPRA_DEMAIS = 0.28
FATOR_MAL_RESOLVIDA = 0.5     # exceção mal resolvida corta a recompra pela metade

# Política padrão por tipo (SPEC.md, "Política de ações"): ação e custo direto dela.
#   reenvio = CMV + frete; refazer personalização = custo de reenvio (parametros.md)
#   devolvido pela transportadora: o produto volta, então só o frete de novo envio (S5)
ACAO_PADRAO = {
    "atraso_entrega": "acionar_transportadora",
    "rastreio_parado": "acionar_transportadora",
    "extravio": "reenviar",
    "devolvido_transportadora": "reenviar",
    "avaria_transporte": "reenviar",
    "vazamento_produto": "reenviar",
    "item_faltante": "reenviar",
    "falha_personalizacao": "refazer_personalizacao",
    "pagamento_pendente": "contatar_cliente",
    "endereco_divergente": "contatar_cliente",
    "ruptura_pos_venda": "contatar_cliente",
}


def prob_cancelamento(dias_uteis: int) -> float:
    """Tabela 'Risco de cancelamento por atraso' (parametros.md)."""
    if dias_uteis <= 0:
        return 0.0
    if dias_uteis <= 2:
        return 0.04
    if dias_uteis <= 5:
        return 0.10
    if dias_uteis <= 10:
        return 0.22
    return 0.40


def custo_acao(tipo: str, valor: float, frete: float) -> float:
    acao = ACAO_PADRAO[tipo]
    if tipo == "devolvido_transportadora":
        return frete
    if acao in ("reenviar", "refazer_personalizacao"):
        return CMV * valor + frete
    return 0.0


def produto_pendente(tipo: str, entregue: bool) -> bool:
    """S1: o cliente ainda não tem o produto em condições, então a espera dele continua contando.
    A única exceção é o atraso já entregue: o produto chegou e o atraso parou de crescer."""
    return not (tipo == "atraso_entrega" and entregue)


@dataclass(frozen=True)
class CasoRisco:
    order_id: str
    tipo: str
    valor: float
    frete: float
    entregue: bool
    data_prometida: pd.Timestamp
    atraso_atual: int          # dias úteis de atraso contra o prometido, em 30/09/2026
    ticket_medio: float
    alto_valor: bool

    @classmethod
    def da_linha(cls, r) -> "CasoRisco":
        return cls(r.order_id, r.tipo_excecao, float(r.valor), float(r.custo_medio_frete), bool(r.entregue),
                   r.data_prometida, int(r.atraso_du_prometido), float(r.ticket_medio_cliente), bool(r.cliente_alto_valor))


def atraso_no_dia(c: CasoRisco, t: int) -> int:
    """Dias úteis de atraso (contra o prazo prometido ao cliente) se o caso for tratado t dias úteis depois de 30/09."""
    if not produto_pendente(c.tipo, c.entregue):
        return c.atraso_atual
    return calendario.dias_uteis_atraso(c.data_prometida, calendario.somar_dias_uteis(DATA_REFERENCIA, t))


def recompra_perdida(c: CasoRisco) -> float:
    """Estimativa: receita de um pedido futuro que deixa de vir se a exceção for mal resolvida (S3)."""
    p = P_RECOMPRA_ALTO_VALOR if c.alto_valor else P_RECOMPRA_DEMAIS
    return p * FATOR_MAL_RESOLVIDA * c.ticket_medio


def perda_esperada(c: CasoRisco, t: int) -> dict:
    """Perda esperada (R$) se o caso for tratado no dia útil t (t = 0 é 30/09/2026).

    S2: tratar o caso trava o atraso no dia do tratamento (cliente informado e solução em andamento).
    S3: o cliente que cancela é a exceção mal resolvida; ele recebe o reembolso e a recompra cai pela metade.
    Sem dupla contagem: quem cancela é reembolsado e não recebe reenvio.
    """
    pc = prob_cancelamento(atraso_no_dia(c, t))
    reembolso = pc * c.valor
    recompra = pc * recompra_perdida(c)
    resolucao = (1 - pc) * custo_acao(c.tipo, c.valor, c.frete)
    return {"p_cancelamento": pc, "reembolso": reembolso, "recompra": recompra,
            "resolucao": resolucao, "total": reembolso + recompra + resolucao}


def custo_de_espera(c: CasoRisco, t: int, dias: int = 1) -> float:
    """Quanto a perda esperada cresce se o caso esperar `dias` dias úteis a mais a partir do dia t."""
    return perda_esperada(c, t + dias)["total"] - perda_esperada(c, t)["total"]
