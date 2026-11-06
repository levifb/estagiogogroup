"""Cliente Groq: tool calling com limite de passos, JSON validado e cadeia de modelos de reserva.

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
# Cadeia de reserva: se o modelo da vez bater no limite, ficar fora do ar ou for removido pelo Groq,
# a chamada passa para o próximo. O 20b passou pelo mesmo eval (LOG.md, 2026-11-05 20:17); o qwen não.
MODELOS = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]
MAX_FERRAMENTAS = 3


def _env_float(nome: str, padrao: float) -> float:
    try:
        return float(os.getenv(nome, padrao))
    except ValueError:
        return padrao


def modelo() -> str:
    return os.getenv("GROQ_MODEL") or MODELO_PADRAO


def cadeia() -> list[str]:
    """Modelos na ordem em que são tentados: o configurado primeiro, depois a reserva."""
    primeiro = modelo()
    return [primeiro] + [m for m in MODELOS if m != primeiro]


def modelo_usado(rastro: list[dict]) -> Optional[str]:
    """Qual modelo respondeu: o da última chamada bem-sucedida registrada no rastro."""
    return next((p["modelo"] for p in reversed(rastro) if p.get("modelo") and p["etapa"].startswith("modelo")), None)


def disponivel() -> bool:
    return bool(os.getenv("GROQ_API_KEY"))


def _cliente():
    from groq import Groq
    # A API publicada usa um tempo menor (GROQ_TIMEOUT_S), porque a tela desiste em 25 s.
    return Groq(api_key=os.getenv("GROQ_API_KEY"), timeout=_env_float("GROQ_TIMEOUT_S", 60), max_retries=0)


def _espera_429(e) -> float:
    try:
        ra = e.response.headers.get("retry-after")
        if ra:
            return float(ra) + 0.5
    except Exception:
        pass
    return 20.0


MSG_LIMITE = "o modelo atingiu o limite de uso do plano gratuito; a decisão exibida é a gravada"
MSG_REDE = "não foi possível falar com o modelo (rede ou tempo esgotado)"
MSG_FORA = "o modelo está fora do ar ou foi removido pelo Groq"


def _modelo_sumiu(e) -> bool:
    """400/403/404 que dizem respeito ao modelo (removido, inexistente, bloqueado), e não ao pedido."""
    from groq import BadRequestError, NotFoundError, PermissionDeniedError
    if isinstance(e, NotFoundError):
        return True
    if isinstance(e, (BadRequestError, PermissionDeniedError)):
        texto = f"{getattr(e, 'body', '')} {e}".lower()
        return any(p in texto for p in ("decommissioned", "model_not_found", "does not exist", "not supported",
                                       "permission_blocked", "model_terminated"))
    return False


def _chamar_um(cli, modelo_atual: str, ultimo: bool, **kw):
    """Uma chamada a um modelo. Devolve (resposta, erro, vale_trocar_de_modelo)."""
    from groq import APIConnectionError, APITimeoutError, InternalServerError, RateLimitError
    espera_max = _env_float("GROQ_ESPERA_MAX_S", 65)  # espera maior (ex.: limite DIÁRIO) não vale a pena
    if not modelo_atual.startswith("openai/gpt-oss"):
        kw.pop("reasoning_effort", None)  # parâmetro da família gpt-oss; outro modelo pode recusar o valor
    for tentativa in range(3):
        try:
            return cli.chat.completions.create(model=modelo_atual, **kw), None, False
        except RateLimitError as e:
            log.warning("429 do Groq (%s): %s", modelo_atual, e)
            espera = _espera_429(e)
            if not ultimo:  # outro modelo tem cota própria: troca na hora em vez de esperar
                return None, MSG_LIMITE, True
            if tentativa == 2 or espera > espera_max:
                return None, MSG_LIMITE, True
            time.sleep(espera)
        except (APIConnectionError, APITimeoutError) as e:
            log.warning("rede/timeout (%s): %s", modelo_atual, e)
            if tentativa >= 1:
                return None, MSG_REDE, True
            time.sleep(2)
        except InternalServerError as e:  # 5xx: modelo fora do ar ou sobrecarregado
            log.warning("5xx do Groq (%s): %s", modelo_atual, e)
            return None, MSG_FORA, True
        except Exception as e:
            if _modelo_sumiu(e):
                log.warning("modelo indisponível (%s): %s", modelo_atual, e)
                return None, MSG_FORA, True
            log.warning("erro da API (%s): %s", modelo_atual, e)  # ex.: 400 do pedido; trocar não ajuda
            return None, f"o modelo devolveu um erro ({type(e).__name__})", False
    return None, "falha desconhecida", False


def _chamar(cli, estado: dict, rastro: list, **kw):
    """Chama o modelo da vez; se ele falhar por limite, queda ou remoção, passa para o próximo da cadeia.
    `estado["i"]` guarda a posição, para a decisão inteira ficar com o mesmo modelo depois de uma troca."""
    modelos = estado["cadeia"]
    while estado["i"] < len(modelos):
        atual = modelos[estado["i"]]
        resp, erro, trocar = _chamar_um(cli, atual, estado["i"] == len(modelos) - 1, **kw)
        if resp is not None:
            return resp, None, atual
        if not trocar:
            return None, erro, atual
        estado["i"] += 1
        if estado["i"] < len(modelos):
            rastro.append({"etapa": "troca_de_modelo", "de": atual, "para": modelos[estado["i"]], "motivo": erro})
    return None, erro, None


def _extrair_json(texto: str) -> str:
    texto = re.sub(r"<think>.*?</think>", "", texto or "", flags=re.S).strip()  # raciocínio exposto (qwen)
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
    base = dict(temperature=0, reasoning_effort=reasoning_effort)
    estado = {"cadeia": cadeia(), "i": 0}
    usadas = 0

    # 1) Investigação: o modelo pode chamar até MAX_FERRAMENTAS ferramentas.
    while tools:
        t0 = time.time()
        extra = {"tools": tools, "tool_choice": "auto"} if usadas < MAX_FERRAMENTAS else {}
        resp, erro, usado = _chamar(cli, estado, rastro, messages=msgs, **extra, **base)
        if erro:
            rastro.append({"etapa": "erro", "detalhe": erro})
            return None, rastro
        msg = resp.choices[0].message
        rastro.append({"etapa": "modelo", "modelo": usado, "segundos": round(time.time() - t0, 2),
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
            resp, erro, usado = _chamar(cli, estado, rastro, messages=msgs, response_format={"type": "json_object"}, **base)
            if erro:
                rastro.append({"etapa": "erro", "detalhe": erro})
                return None, rastro
            texto = resp.choices[0].message.content
            rastro.append({"etapa": "modelo_json", "modelo": usado, "segundos": round(time.time() - t0, 2),
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
