"""Cliente Groq: tool calling com limite de passos, JSON validado e recuo em 429.

Nunca levanta exceção para quem chama: devolve (objeto validado ou None, rastro).
"""

import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Callable, Optional, Type

from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

log = logging.getLogger("agente.llm")
MODELO_PADRAO = "openai/gpt-oss-120b"  # escolha registrada no LOG.md (2026-11-05)
MAX_FERRAMENTAS = 3
TIMEOUT_S = 60


def modelo() -> str:
    return os.getenv("GROQ_MODEL") or MODELO_PADRAO


def disponivel() -> bool:
    return bool(os.getenv("GROQ_API_KEY"))


def _cliente():
    from groq import Groq
    return Groq(api_key=os.getenv("GROQ_API_KEY"), timeout=TIMEOUT_S, max_retries=0)


def _espera_429(e) -> float:
    try:
        ra = e.response.headers.get("retry-after")
        if ra:
            return min(float(ra) + 0.5, 65.0)
    except Exception:
        pass
    return 20.0


def _chamar(cli, **kw):
    """Uma chamada com até 2 novas tentativas em 429 ou erro de rede."""
    from groq import APIConnectionError, APITimeoutError, RateLimitError
    for tentativa in range(3):
        try:
            return cli.chat.completions.create(**kw), None
        except RateLimitError as e:
            log.warning("429 do Groq: %s", e)
            if tentativa == 2:
                return None, "o modelo atingiu o limite de uso do plano gratuito; tente de novo em um minuto"
            time.sleep(_espera_429(e))
        except (APIConnectionError, APITimeoutError) as e:
            log.warning("rede/timeout: %s", e)
            if tentativa == 2:
                return None, "não foi possível falar com o modelo (rede ou tempo esgotado)"
            time.sleep(2 ** (tentativa + 1))
        except Exception as e:  # erro da API (ex.: 400) não melhora com nova tentativa
            log.warning("erro da API: %s", e)
            return None, f"o modelo devolveu um erro ({type(e).__name__})"
    return None, "falha desconhecida"


def _extrair_json(texto: str) -> str:
    texto = (texto or "").strip()
    m = re.search(r"\{.*\}", texto, flags=re.S)
    return m.group(0) if m else texto


def gerar(mensagens: list[dict], esquema: Type[BaseModel], tools: Optional[list] = None,
          executar_ferramenta: Optional[Callable[[str, str], str]] = None,
          reasoning_effort: str = "low") -> tuple[Optional[BaseModel], list[dict]]:
    rastro: list[dict] = []
    if not disponivel():
        rastro.append({"etapa": "erro", "detalhe": "GROQ_API_KEY ausente"})
        return None, rastro
    cli = _cliente()
    msgs = list(mensagens)
    base = dict(model=modelo(), temperature=0, reasoning_effort=reasoning_effort)
    usadas = 0

    # 1) Investigação: o modelo pode chamar até MAX_FERRAMENTAS ferramentas.
    while tools:
        t0 = time.time()
        extra = {"tools": tools, "tool_choice": "auto"} if usadas < MAX_FERRAMENTAS else {}
        resp, erro = _chamar(cli, messages=msgs, **extra, **base)
        if erro:
            rastro.append({"etapa": "erro", "detalhe": erro})
            return None, rastro
        msg = resp.choices[0].message
        rastro.append({"etapa": "modelo", "segundos": round(time.time() - t0, 2),
                       "tokens": getattr(resp.usage, "total_tokens", None),
                       "chamou_ferramentas": bool(msg.tool_calls)})
        if not msg.tool_calls:
            texto = msg.content
            break
        msgs.append({"role": "assistant", "content": msg.content or "",
                     "tool_calls": [tc.model_dump() for tc in msg.tool_calls]})
        for tc in msg.tool_calls:
            usadas += 1
            saida = executar_ferramenta(tc.function.name, tc.function.arguments) if executar_ferramenta else "{}"
            rastro.append({"etapa": "ferramenta", "nome": tc.function.name,
                           "argumentos": tc.function.arguments, "resposta": json.loads(saida)})
            msgs.append({"role": "tool", "tool_call_id": tc.id, "content": saida})
    else:
        texto = None

    # 2) Decisão em JSON validado: a resposta da investigação, ou uma chamada em modo JSON.
    for tentativa in range(2):
        if texto is None:
            t0 = time.time()
            resp, erro = _chamar(cli, messages=msgs, response_format={"type": "json_object"}, **base)
            if erro:
                rastro.append({"etapa": "erro", "detalhe": erro})
                return None, rastro
            texto = resp.choices[0].message.content
            rastro.append({"etapa": "modelo_json", "segundos": round(time.time() - t0, 2),
                           "tokens": getattr(resp.usage, "total_tokens", None)})
        try:
            obj = esquema.model_validate_json(_extrair_json(texto))
            rastro.append({"etapa": "json_valido", "tentativa": tentativa + 1})
            return obj, rastro
        except (ValidationError, ValueError) as e:
            rastro.append({"etapa": "json_invalido", "tentativa": tentativa + 1, "erro": str(e)[:500], "bruto": (texto or "")[:800]})
            msgs.append({"role": "assistant", "content": texto or ""})
            msgs.append({"role": "user", "content": f"A resposta não passou na validação: {str(e)[:400]}. "
                                                    "Responda de novo somente com o JSON no formato pedido."})
            texto = None
    return None, rastro
