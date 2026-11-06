"""API publicada: só o processamento ao vivo de um caso da fila do dia.

Todo o resto da tela vem de JSON estático (src/exportar.py). Esta função não usa
pandas nem scipy: lê a ficha pré-calculada e chama o mesmo núcleo do eval, decidir().
"""

import json
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DADOS = Path(__file__).resolve().parent / "_dados"
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("FERRAMENTAS_PRECALC", str(DADOS / "ferramentas.json"))
# A tela desiste em 25 s: aqui não vale esperar a cota liberar; cada modelo tem 10 s antes do próximo.
os.environ.setdefault("GROQ_ESPERA_MAX_S", "0")
os.environ.setdefault("GROQ_TIMEOUT_S", "10")

from fastapi import FastAPI  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402

from src.agente import llm  # noqa: E402
from src.agente.pipeline import decidir  # noqa: E402

app = FastAPI(title="Mesa de exceções")
_FICHAS: dict | None = None


def fichas() -> dict:
    global _FICHAS
    if _FICHAS is None:
        _FICHAS = json.loads((DADOS / "fichas.json").read_text(encoding="utf-8"))
    return _FICHAS


@app.get("/api/saude")
def saude():
    return {"ok": True, "modelo": llm.modelo(), "modelos_reserva": llm.cadeia()[1:], "chave_configurada": llm.disponivel(), "casos_na_fila": len(fichas())}


@app.post("/api/processar/{order_id}")
def processar_ao_vivo(order_id: str):
    ficha = fichas().get(order_id)
    if ficha is None:
        return JSONResponse({"erro": "só os casos da fila de hoje podem ser processados ao vivo"}, status_code=404)
    if not llm.disponivel():
        return JSONResponse({"erro": "modelo indisponível nesta publicação; a tela mostra a decisão em cache"}, status_code=503)
    r = decidir(ficha, modo="ao_vivo", gravar=False)
    if r.fonte != "ao_vivo":
        return JSONResponse({"erro": r.erro or "o modelo não respondeu; a tela mostra a decisão em cache",
                             "resultado": r.model_dump(mode="json")}, status_code=503)
    return r.model_dump(mode="json")
