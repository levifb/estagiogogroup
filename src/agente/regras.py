"""Humano no loop (SPEC.md, H1 a H7). Sempre em código, nunca só no prompt.

A primeira regra que se aplica decide. O código pode rebaixar uma ação automática
para escalar_humano; nunca transforma um escalonamento em ação automática.
"""

import re
from typing import Optional

from src.agente.esquemas import Acao, Decisao

LIMITE_REEMBOLSO = 228.0   # N13: percentil 95 do valor do pedido com exceção
LIMITE_REENVIO = 73.21     # N68: percentil 95 do custo de reenvio (24% do valor + frete)
PRAZO_POLITICA_DIAS = 7    # reenvio de avaria/vazamento/faltante até 7 dias do recebimento (S9)
TETO_ATRASO_DU = 10        # acima disso o risco está no teto (S8)
NAO_ENTREGUE = {"extravio", "rastreio_parado", "devolvido_transportadora"}
EXIGE_FOTO = {"avaria_transporte", "vazamento_produto", "item_faltante", "falha_personalizacao"}

TIPO = {
    "atraso_entrega": "atraso na entrega", "rastreio_parado": "rastreio parado", "extravio": "extravio",
    "devolvido_transportadora": "devolvido pela transportadora", "avaria_transporte": "avaria no transporte",
    "vazamento_produto": "produto vazou", "item_faltante": "item faltando",
    "falha_personalizacao": "falha na personalização", "pagamento_pendente": "pagamento pendente",
    "endereco_divergente": "endereço divergente", "ruptura_pos_venda": "sem estoque após a venda",
}
STATUS = {"aberta": "aberta", "em_analise": "em análise", "aguardando_transportadora": "aguardando a transportadora",
          "aguardando_cliente": "aguardando o cliente"}

# "não precisa enviar foto", "dispensamos a foto", "sem necessidade de foto"...
_NEGA_FOTO = re.compile(r"(n[ãa]o\s+(?:precisa|[ée]\s+necess[áa]ri[oa]|ser[áa]\s+necess[áa]ri[oa])[^.!?]*foto"
                        r"|dispens\w*[^.!?]*foto|sem\s+(?:necessidade\s+de\s+)?(?:enviar\s+)?foto)", re.I)


def _reais(v: float) -> str:
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def mensagem_pede_foto(mensagem: Optional[str]) -> bool:
    msg = mensagem or ""
    return bool(re.search(r"\bfoto", msg, re.I)) and not _NEGA_FOTO.search(msg)


def regra_humano(ficha: dict, d: Optional[Decisao]) -> Optional[tuple[str, str]]:
    """Devolve (id_regra, motivo) se o caso precisa de uma pessoa, ou None."""
    exc, ent, cli, ped, custos = ficha["excecao"], ficha["entrega"], ficha["cliente"], ficha["pedido"], ficha.get("custos_acoes", {})
    tipo = TIPO.get(exc["tipo"], exc["tipo"])

    if exc["status_incoerente_com_tipo"]:
        return "H1", (f"o registro diz \"{STATUS.get(exc['status'], exc['status'])}\", o que não combina com "
                      f"\"{tipo}\"; conferir o registro antes de agir")
    if ent["entregue"] and not ent.get("data_entrega"):
        return "H1", "o registro diz que o pedido foi entregue, mas não tem data de entrega; conferir antes de agir"
    if ent["entregue"] and exc["tipo"] in NAO_ENTREGUE:
        return "H1", f"\"{tipo}\" implica pedido não entregue, mas o registro diz que foi entregue; conferir antes de agir"
    if d is not None and d.acao == Acao.reembolsar and ped["valor_pago"] > LIMITE_REEMBOLSO:
        return "H2", f"reembolso de {_reais(ped['valor_pago'])}, acima do limite de {_reais(LIMITE_REEMBOLSO)}"
    if d is not None and d.acao in (Acao.reenviar, Acao.refazer_personalizacao):
        # Se é a ação padrão do tipo, vale o custo dela (ex.: devolução = só o frete, S5).
        custo = custos.get("custo_acao_padrao") if d.acao.value == custos.get("acao_padrao_do_tipo") else custos.get(d.acao.value)
        if custo is not None and custo > LIMITE_REENVIO:
            return "H2b", f"reenvio com custo estimado de {_reais(custo)}, acima do limite de {_reais(LIMITE_REENVIO)}"
    if d is not None and d.acao == Acao.reembolsar and cli["alto_valor_acima_1500"]:
        return "H3", "reembolso para cliente com receita acumulada acima de R$ 1.500"
    if exc["tipo"] == "atraso_entrega" and not ent["entregue"] and ent["dias_uteis_atraso_vs_prometido"] > TETO_ATRASO_DU:
        return "H4", f"{ent['dias_uteis_atraso_vs_prometido']} dias úteis de atraso sem entrega; decidir entre reenviar e reembolsar"
    dr = ent["dias_entre_recebimento_e_reclamacao"]
    if exc["tipo"] in ("avaria_transporte", "vazamento_produto", "item_faltante") and dr is not None and dr > PRAZO_POLITICA_DIAS:
        return "H5", f"reclamação {dr} dias após o recebimento, fora da política de 7 dias"
    if d is None:
        return "H6", "o modelo não devolveu uma decisão válida"
    if d.confianca == "baixa" or d.precisa_humano or d.acao == Acao.escalar_humano:
        return "H6", d.motivo_humano or "o agente pediu revisão"
    if exc["tipo"] in EXIGE_FOTO and d.acao in (Acao.reenviar, Acao.refazer_personalizacao) \
            and not mensagem_pede_foto(d.mensagem_cliente):
        return "H7", "a mensagem do agente não pede a foto que a política exige antes do reenvio"
    return None
