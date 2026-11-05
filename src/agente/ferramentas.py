"""Ferramentas que o modelo pode chamar para aprofundar um caso. Funções puras sobre src/dados/."""

import json
import os
from functools import lru_cache
from pathlib import Path

_DIMENSOES = {
    "maquina": ["maquina"],
    "lote": ["sku", "lote_produto"],
    "turno_cd": ["cd", "turno"],
    "transportadora_uf": ["transportadora", "uf"],
}


# Na função publicada não há pandas: as respostas das ferramentas para os casos da fila
# vêm pré-calculadas em JSON (src/exportar.py). Localmente, são calculadas na hora.
PRECALC = os.getenv("FERRAMENTAS_PRECALC")


@lru_cache(maxsize=1)
def _precalc() -> dict:
    return json.loads(Path(PRECALC).read_text(encoding="utf-8")) if PRECALC else {}


@lru_cache(maxsize=1)
def _df():
    from src.dados.base import base_trabalho
    return base_trabalho().set_index("order_id", drop=False)


def historico_cliente(customer_id: str) -> dict:
    df = _df()
    do_cliente = df[df["customer_id"] == customer_id]
    if do_cliente.empty:
        return {"erro": f"cliente {customer_id} não encontrado"}
    r = do_cliente.iloc[0]
    return {
        "customer_id": customer_id,
        "n_pedidos": int(r["n_pedidos"]),
        "receita_acumulada": round(float(r["receita_acumulada"]), 2),
        "primeiro_pedido": r["data_primeiro_pedido"].strftime("%d/%m/%Y"),
        "contatos_atendimento_12m": int(r["n_contatos_atendimento"]),
        "excecoes_abertas": [
            {"order_id": o, "tipo": x["tipo_excecao"], "status": x["status"], "valor": round(float(x["valor"]), 2)}
            for o, x in do_cliente.iterrows()
        ],
    }


def casos_parecidos(order_id: str, dimensao: str) -> dict:
    df = _df()
    if order_id not in df.index:
        return {"erro": f"pedido {order_id} não encontrado"}
    if dimensao not in _DIMENSOES:
        return {"erro": f"dimensao deve ser uma de {sorted(_DIMENSOES)}"}
    cols = _DIMENSOES[dimensao]
    alvo = df.loc[order_id]
    if any(alvo[c] is None or alvo[c] != alvo[c] for c in cols):  # NaN
        return {"erro": f"o pedido não tem {dimensao} (ex.: máquina só existe em pedidos Gocase)"}
    sub = df.dropna(subset=cols)
    mesmo = sub[(sub[cols] == alvo[cols]).all(axis=1)]
    tipo = alvo["tipo_excecao"]
    taxa_grupo = (mesmo["tipo_excecao"] == tipo).mean()
    resto = sub.drop(mesmo.index)
    taxa_base = (resto["tipo_excecao"] == tipo).mean() if len(resto) else 0.0
    return {
        "grupo": {c: alvo[c] for c in cols},
        "excecoes_no_grupo": int(len(mesmo)),
        "do_mesmo_tipo": int((mesmo["tipo_excecao"] == tipo).sum()),
        "proporcao_do_tipo_no_grupo": round(float(taxa_grupo), 3),
        "proporcao_do_tipo_nos_demais": round(float(taxa_base), 3),
        "tipos_no_grupo": mesmo["tipo_excecao"].value_counts().head(5).to_dict(),
    }


TOOLS = [
    {"type": "function", "function": {
        "name": "historico_cliente",
        "description": "Outras exceções abertas do mesmo cliente e o histórico dele (pedidos, receita, contatos).",
        "parameters": {"type": "object", "properties": {"customer_id": {"type": "string"}}, "required": ["customer_id"]},
    }},
    {"type": "function", "function": {
        "name": "casos_parecidos",
        "description": "Exceções do mesmo grupo (máquina, lote do SKU, CD+turno ou transportadora+UF), com a proporção do mesmo tipo de exceção no grupo e nos demais.",
        "parameters": {"type": "object", "properties": {
            "order_id": {"type": "string"},
            "dimensao": {"type": "string", "enum": sorted(_DIMENSOES)},
        }, "required": ["order_id", "dimensao"]},
    }},
]

_FUNCOES = {"historico_cliente": historico_cliente, "casos_parecidos": casos_parecidos}


def chave_precalc(nome: str, args: dict) -> str:
    return nome + "|" + "|".join(f"{k}={args[k]}" for k in sorted(args))


def precalcular(order_ids: list[str], customer_ids: list[str]) -> dict:
    out = {chave_precalc("historico_cliente", {"customer_id": c}): historico_cliente(c) for c in set(customer_ids)}
    for o in order_ids:
        for d in _DIMENSOES:
            out[chave_precalc("casos_parecidos", {"order_id": o, "dimensao": d})] = casos_parecidos(o, d)
    return json.loads(json.dumps(out, ensure_ascii=False, default=str))


def executar(nome: str, argumentos: str) -> str:
    """Executa uma chamada do modelo. Erros voltam como texto legível para o modelo, nunca como exceção."""
    if nome not in _FUNCOES:
        return json.dumps({"erro": f"ferramenta '{nome}' não existe; use {sorted(_FUNCOES)}"}, ensure_ascii=False)
    try:
        args = json.loads(argumentos or "{}")
        if PRECALC:
            chave = chave_precalc(nome, args)
            resp = _precalc().get(chave, {"erro": "consulta não disponível na versão publicada; use os dados da ficha"})
            return json.dumps(resp, ensure_ascii=False)
        return json.dumps(_FUNCOES[nome](**args), ensure_ascii=False, default=str)
    except Exception as e:  # argumento inválido do modelo
        return json.dumps({"erro": f"argumentos inválidos para {nome}: {e}"}, ensure_ascii=False)
