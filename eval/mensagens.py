"""Checagens automáticas da mensagem ao cliente, tiradas das regras do prompt de decisão.

Cada checagem devolve o nome da regra quebrada. Lista vazia = mensagem sem problema detectável.
"""

import re

from src.agente.regras import mensagem_pede_foto

JARGAO = re.compile(r"\bSLA\b|\bP0\d\b|padr[aã]o de causa|dias [úu]teis de atraso|probabilidade|perda esperada|"
                    r"custo de esperar|\bficha\b|escalar|\bH\d\b", re.I)
DATA = re.compile(r"\b(\d{2}/\d{2})(?:/\d{4})?\b")
REAIS = re.compile(r"R\$\s?([\d\.]+,\d{2}|[\d\.]+)")
PEDE_FOTO = {"avaria_transporte", "vazamento_produto", "item_faltante", "falha_personalizacao"}


def _datas_da_ficha(ficha: dict) -> set[str]:
    out = set()
    for secao in ficha.values():
        if isinstance(secao, dict):
            for v in secao.values():
                if isinstance(v, str):
                    out |= set(DATA.findall(v))
    return out


def _valores_da_ficha(ficha: dict) -> set[float]:
    out = set()
    for secao in ficha.values():
        if isinstance(secao, dict):
            for v in secao.values():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    out.add(round(float(v), 2))
    return out


def _num(txt: str) -> float:
    return round(float(txt.replace(".", "").replace(",", ".")), 2)


def checar(ficha: dict, acao: str, mensagem: str | None) -> list[str]:
    if acao in ("aguardar", "escalar_humano"):
        return []
    msg = (mensagem or "").strip()
    if not msg:
        return ["sem_mensagem"]
    falhas = []
    marca = ficha["pedido"]["marca"]
    if not msg.rstrip(" .!").endswith(f"Equipe {marca}"):
        falhas.append("assinatura_errada")
    if JARGAO.search(msg):
        falhas.append("jargao_interno")
    if set(DATA.findall(msg)) - _datas_da_ficha(ficha):
        falhas.append("data_fora_da_ficha")
    valores = _valores_da_ficha(ficha)
    if any(_num(v) not in valores for v in REAIS.findall(msg)):
        falhas.append("valor_fora_da_ficha")
    tipo = ficha["excecao"]["tipo"]
    if tipo in PEDE_FOTO and acao in ("reenviar", "refazer_personalizacao") and not mensagem_pede_foto(msg):
        falhas.append("nao_pediu_foto")  # inclui "não precisa enviar foto"
    ent = ficha["entrega"]
    if tipo == "atraso_entrega" and not ent["entregue"] and ent["dentro_do_sla_contratado"]:
        prazo = ent["prazo_correto_pelo_sla_dias_uteis"][:5]
        if prazo not in msg:
            falhas.append("nao_informou_prazo_correto")
    frases = [f for f in re.split(r"(?<=[.!?])\s+", msg) if f.strip()]
    if len(frases) > 6:  # 5 frases + assinatura
        falhas.append("longa_demais")
    return falhas
