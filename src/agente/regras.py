"""Humano no loop (SPEC.md, H1 a H6). Sempre em código, nunca só no prompt.

A primeira regra que se aplica decide. O código pode rebaixar uma ação automática
para escalar_humano; nunca transforma um escalonamento em ação automática.
"""

from typing import Optional

from src.agente.esquemas import Acao, Decisao

LIMITE_REEMBOLSO = 228.0  # N13: percentil 95 do valor do pedido com exceção
PRAZO_POLITICA_DIAS = 7   # reenvio de avaria/vazamento/faltante até 7 dias do recebimento (S9)
TETO_ATRASO_DU = 10       # acima disso o risco está no teto (S8)


def regra_humano(ficha: dict, d: Optional[Decisao]) -> Optional[tuple[str, str]]:
    """Devolve (id_regra, motivo) se o caso precisa de uma pessoa, ou None."""
    exc, ent, cli, ped = ficha["excecao"], ficha["entrega"], ficha["cliente"], ficha["pedido"]

    if exc["status_incoerente_com_tipo"]:
        return "H1", f"status '{exc['status']}' não combina com o tipo '{exc['tipo']}'; conferir o registro antes de agir"
    if d is not None and d.acao == Acao.reembolsar and ped["valor_pago"] > LIMITE_REEMBOLSO:
        return "H2", f"reembolso de R$ {ped['valor_pago']:.2f}, acima do limite de R$ {LIMITE_REEMBOLSO:.0f}"
    if d is not None and d.acao == Acao.reembolsar and cli["alto_valor_acima_1500"]:
        return "H3", "reembolso para cliente com receita acumulada acima de R$ 1.500"
    if exc["tipo"] == "atraso_entrega" and not ent["entregue"] and ent["dias_uteis_atraso_vs_prometido"] > TETO_ATRASO_DU:
        return "H4", f"{ent['dias_uteis_atraso_vs_prometido']} dias úteis de atraso sem entrega; decidir entre reenvio e reembolso"
    dr = ent["dias_entre_recebimento_e_reclamacao"]
    if exc["tipo"] in ("avaria_transporte", "vazamento_produto", "item_faltante") and dr is not None and dr > PRAZO_POLITICA_DIAS:
        return "H5", f"reclamação {dr} dias após o recebimento, fora da política de 7 dias"
    if d is None:
        return "H6", "o modelo não devolveu uma decisão válida"
    if d.confianca == "baixa" or d.precisa_humano or d.acao == Acao.escalar_humano:
        return "H6", d.motivo_humano or "o agente pediu revisão"
    return None
