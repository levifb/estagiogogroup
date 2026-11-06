"""processar(): a única entrada do agente. A API e o eval chamam esta mesma função.

Etapas: ficha (código) → investigação e decisão (LLM com ferramentas) → regras de
humano no loop (código) → execução simulada ou fila de aprovação.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Literal

from src.agente import ferramentas, llm, regras
from src.agente.esquemas import Acao, Decisao, Resultado

RAIZ = Path(__file__).resolve().parents[2]
PASTA_CACHE = RAIZ / "demo" / "cache"


@lru_cache(maxsize=None)
def carregar_prompt(nome: str) -> tuple[int, list[str], str]:
    """Lê src/agente/prompts/<nome>.md: cabeçalho (versao, exemplos) e corpo."""
    texto = (Path(__file__).parent / "prompts" / f"{nome}.md").read_text(encoding="utf-8")
    cab, corpo = texto.split("\n---\n", 1)
    meta = dict(l.split(":", 1) for l in cab.strip().splitlines())
    exemplos = [e.strip() for e in meta.get("exemplos", "").split(",") if e.strip()]
    return int(meta["versao"]), exemplos, corpo.strip()


def _arquivo_cache(order_id: str, tipo: str, versao: int) -> Path:
    return PASTA_CACHE / f"{order_id}_{tipo}_v{versao}.json"


def ler_cache(order_id: str, tipo: str, versao: int):
    arq = _arquivo_cache(order_id, tipo, versao)
    if not arq.exists():
        return None
    return Resultado.model_validate_json(arq.read_text(encoding="utf-8"))


def gravar_cache(r: Resultado) -> None:
    PASTA_CACHE.mkdir(parents=True, exist_ok=True)
    _arquivo_cache(r.order_id, r.tipo_excecao, r.versao_prompt).write_text(
        r.model_dump_json(indent=1), encoding="utf-8")


def _artefato(acao: Acao, ficha: dict, d: Decisao) -> dict:
    """Execução simulada: o que o sistema faria de verdade, marcado como simulado."""
    ped, ent, custos = ficha["pedido"], ficha["entrega"], ficha["custos_acoes"]
    base = {"simulado": True, "mensagem_cliente": d.mensagem_cliente}
    # Política: avaria, vazamento, faltante e personalização só são refeitos depois da foto do cliente.
    aguarda_foto = ficha["excecao"]["tipo"] in regras.EXIGE_FOTO
    if acao == Acao.reenviar:
        base["ordem"] = {"tipo": "reenvio", "sku": ped["sku"], "transportadora": ent["transportadora"],
                         "custo_estimado": custos["reenviar"],
                         "situacao": "aguardando a foto do cliente" if aguarda_foto else "liberado"}
    elif acao == Acao.refazer_personalizacao:
        base["ordem"] = {"tipo": "nova_producao", "sku": ped["sku"], "evitar_maquina": ped["maquina"],
                         "custo_estimado": custos["refazer_personalizacao"], "situacao": "aguardando a foto do cliente"}
    elif acao == Acao.reembolsar:
        base["ordem"] = {"tipo": "reembolso", "valor": ped["valor_pago"]}
    elif acao == Acao.acionar_transportadora:
        base["ordem"] = {"tipo": "chamado_transportadora", "transportadora": ent["transportadora"],
                         "sla_contratado_dias_uteis": ent["sla_contratado_dias_uteis"],
                         "dias_uteis_alem_do_sla": ent["dias_uteis_atraso_vs_sla_contratado"]}
    return base


def _montar(order_id: str, ficha: dict, decisao, rastro, fonte, versao, erro=None) -> Resultado:
    regra = regras.regra_humano(ficha, decisao)
    if regra:
        acao_final, humano, motivo = Acao.escalar_humano, True, regra[1]
    else:
        acao_final, humano, motivo = decisao.acao, False, None
    artefato = {} if humano else _artefato(acao_final, ficha, decisao)
    if humano and decisao is not None:
        artefato = {"proposta_do_agente": decisao.acao.value, "mensagem_rascunho": decisao.mensagem_cliente}
    return Resultado(order_id=order_id, tipo_excecao=ficha["excecao"]["tipo"], fonte=fonte,
                     decisao_modelo=decisao, acao_final=acao_final, vai_para_humano=humano,
                     motivo_humano=motivo, regra_aplicada=regra[0] if regra else None,
                     artefato=artefato, ficha=ficha, rastro=rastro, versao_prompt=versao, erro=erro)


def reaplicar_regras(r: Resultado) -> Resultado:
    """Recalcula regras e execução de um resultado gravado, sem chamar o modelo."""
    novo = _montar(r.order_id, r.ficha, r.decisao_modelo, r.rastro, r.fonte, r.versao_prompt, erro=r.erro)
    return novo.model_copy(update={"modelo": r.modelo or "openai/gpt-oss-120b"})


def processar(order_id: str, modo: Literal["ao_vivo", "demo"] = "demo", gravar: bool = True) -> Resultado:
    """Monta a ficha a partir dos dados e decide. Nunca levanta exceção (exceto pedido inexistente)."""
    from src.agente.ficha import montar_ficha  # importa pandas/scipy só quando há dados locais
    return decidir(montar_ficha(order_id), modo=modo, gravar=gravar)


def decidir(ficha: dict, modo: Literal["ao_vivo", "demo"] = "demo", gravar: bool = True) -> Resultado:
    """Núcleo do agente a partir de uma ficha pronta. É o que a API publicada chama."""
    versao, _, sistema = carregar_prompt("decisao")
    order_id = ficha["pedido"]["order_id"]
    tipo = ficha["excecao"]["tipo"]

    if modo == "demo":
        cache = ler_cache(order_id, tipo, versao)
        if cache is not None:
            return cache.model_copy(update={"fonte": "cache"})
        return _montar(order_id, ficha, None, [{"etapa": "sem_cache"}], "sem_modelo", versao,
                       erro="caso fora do cache do modo demo")

    mensagens = [
        {"role": "system", "content": sistema},
        {"role": "user", "content": "<ficha>\n" + json.dumps(ficha, ensure_ascii=False) + "\n</ficha>"},
    ]
    decisao, rastro = llm.gerar(mensagens, Decisao, tools=ferramentas.TOOLS,
                                executar_ferramenta=ferramentas.executar)
    if decisao is None:
        cache = ler_cache(order_id, tipo, versao)
        if cache is not None:
            return cache.model_copy(update={"fonte": "cache", "rastro": cache.rastro + rastro})
        erro = next((r.get("detalhe") or r.get("erro") for r in reversed(rastro) if r["etapa"] in ("erro", "json_invalido")), None)
        return _montar(order_id, ficha, None, rastro, "sem_modelo", versao, erro=erro)

    r = _montar(order_id, ficha, decisao, rastro, "ao_vivo", versao).model_copy(update={"modelo": llm.modelo()})
    if gravar:
        try:
            gravar_cache(r)
        except OSError:  # sistema de arquivos somente leitura (ex.: função serverless)
            pass
    return r
