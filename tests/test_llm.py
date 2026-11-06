"""Cadeia de modelos de reserva do cliente Groq, sem rede: um cliente falso lança os erros do SDK."""

from types import SimpleNamespace

import httpx
import pytest
from groq import APITimeoutError, AuthenticationError, BadRequestError, InternalServerError, NotFoundError, RateLimitError
from pydantic import BaseModel

from src.agente import llm

REQ = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")


def erro(cls, status, corpo=None, headers=None):
    return cls("erro simulado", response=httpx.Response(status, request=REQ, headers=headers or {}), body=corpo)


class Saida(BaseModel):
    acao: str


def resposta(texto='{"acao": "reenviar"}'):
    msg = SimpleNamespace(content=texto, tool_calls=None)
    return SimpleNamespace(choices=[SimpleNamespace(message=msg)], usage=SimpleNamespace(total_tokens=10))


class ClienteFalso:
    """Cada modelo tem uma lista de efeitos (exceção ou resposta), consumidos em ordem."""

    def __init__(self, efeitos: dict):
        self.efeitos = {m: list(v) for m, v in efeitos.items()}
        self.chamadas: list[dict] = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kw):
        self.chamadas.append(kw)
        fila = self.efeitos.get(kw["model"], [])
        efeito = fila.pop(0) if fila else resposta()
        if isinstance(efeito, Exception):
            raise efeito
        return efeito


@pytest.fixture
def cliente(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "teste")
    monkeypatch.delenv("GROQ_MODEL", raising=False)
    monkeypatch.setenv("GROQ_ESPERA_MAX_S", "0")
    monkeypatch.setattr(llm.time, "sleep", lambda s: None)

    def montar(efeitos):
        falso = ClienteFalso(efeitos)
        monkeypatch.setattr(llm, "_cliente", lambda: falso)
        return falso
    return montar


MSGS = [{"role": "user", "content": "oi"}]
M120, M20, QWEN = llm.MODELOS


def test_cadeia_comeca_pelo_modelo_configurado(monkeypatch):
    monkeypatch.delenv("GROQ_MODEL", raising=False)
    assert llm.cadeia() == [M120, M20, QWEN]
    monkeypatch.setenv("GROQ_MODEL", M20)
    assert llm.cadeia() == [M20, M120, QWEN]


def test_sem_erro_responde_o_primeiro(cliente):
    falso = cliente({})
    obj, rastro = llm.gerar(MSGS, Saida)
    assert obj.acao == "reenviar"
    assert llm.modelo_usado(rastro) == M120
    assert [c["model"] for c in falso.chamadas] == [M120]


def test_limite_passa_para_o_proximo(cliente):
    falso = cliente({M120: [erro(RateLimitError, 429, headers={"retry-after": "3000"})]})
    obj, rastro = llm.gerar(MSGS, Saida)
    assert obj is not None and llm.modelo_usado(rastro) == M20
    assert [c["model"] for c in falso.chamadas] == [M120, M20]
    troca = next(p for p in rastro if p["etapa"] == "troca_de_modelo")
    assert troca["de"] == M120 and troca["para"] == M20 and "limite" in troca["motivo"]


def test_modelo_removido_e_fora_do_ar_chegam_ao_qwen(cliente):
    removido = erro(BadRequestError, 400, corpo={"error": {"code": "model_decommissioned"}})
    falso = cliente({M120: [removido], M20: [erro(InternalServerError, 503)]})
    obj, rastro = llm.gerar(MSGS, Saida)
    assert obj is not None and llm.modelo_usado(rastro) == QWEN
    assert "reasoning_effort" not in falso.chamadas[-1]  # parâmetro só da família gpt-oss
    assert "reasoning_effort" in falso.chamadas[0]


def test_modelo_inexistente_404_troca(cliente):
    cliente({M120: [erro(NotFoundError, 404)]})
    obj, rastro = llm.gerar(MSGS, Saida)
    assert llm.modelo_usado(rastro) == M20


def test_timeout_tenta_de_novo_e_depois_troca(cliente):
    t = APITimeoutError(request=REQ)
    falso = cliente({M120: [t, t]})
    obj, rastro = llm.gerar(MSGS, Saida)
    assert [c["model"] for c in falso.chamadas] == [M120, M120, M20]
    assert llm.modelo_usado(rastro) == M20


def test_todos_no_limite_devolve_erro_de_limite(cliente):
    lim = lambda: erro(RateLimitError, 429, headers={"retry-after": "3000"})  # noqa: E731
    cliente({M120: [lim()], M20: [lim()], QWEN: [lim()]})
    obj, rastro = llm.gerar(MSGS, Saida)
    assert obj is None
    assert "limite" in rastro[-1]["detalhe"]  # o lote --paciente depende dessa palavra
    assert sum(p["etapa"] == "troca_de_modelo" for p in rastro) == 2


def test_erro_do_pedido_nao_troca_de_modelo(cliente):
    falso = cliente({M120: [erro(BadRequestError, 400, corpo={"error": {"code": "invalid_request"}})]})
    obj, rastro = llm.gerar(MSGS, Saida)
    assert obj is None and [c["model"] for c in falso.chamadas] == [M120]


def test_chave_invalida_nao_troca_de_modelo(cliente):
    falso = cliente({M120: [erro(AuthenticationError, 401)]})
    obj, _ = llm.gerar(MSGS, Saida)
    assert obj is None and len(falso.chamadas) == 1


def test_json_com_raciocinio_exposto(cliente):
    cliente({M120: [erro(NotFoundError, 404)], M20: [erro(NotFoundError, 404)],
             QWEN: [resposta('<think>pensando {em} algo</think>\n{"acao": "aguardar"}')]})
    obj, rastro = llm.gerar(MSGS, Saida)
    assert obj.acao == "aguardar" and llm.modelo_usado(rastro) == QWEN


def test_depois_da_troca_a_decisao_fica_no_mesmo_modelo(cliente):
    falso = cliente({M120: [erro(RateLimitError, 429, headers={"retry-after": "3000"})],
                     M20: [resposta("isto não é json")]})
    obj, rastro = llm.gerar(MSGS, Saida)
    # 1ª resposta inválida, nova tentativa em modo JSON: continua no 20b, não volta ao 120b
    assert obj is not None
    assert [c["model"] for c in falso.chamadas] == [M120, M20, M20]
