"""Contratos de saída do modelo e do pipeline. Toda saída do LLM passa por aqui."""

from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, model_validator


class Acao(str, Enum):
    reenviar = "reenviar"
    refazer_personalizacao = "refazer_personalizacao"
    reembolsar = "reembolsar"
    acionar_transportadora = "acionar_transportadora"
    contatar_cliente = "contatar_cliente"
    aguardar = "aguardar"
    escalar_humano = "escalar_humano"


class Decisao(BaseModel):
    acao: Acao
    justificativa: str = Field(min_length=10, max_length=600)
    mensagem_cliente: Optional[str] = Field(default=None, max_length=900)
    pertence_a_padrao: Optional[str] = None
    confianca: Literal["alta", "media", "baixa"]
    precisa_humano: bool
    motivo_humano: Optional[str] = None

    @model_validator(mode="after")
    def _coerente(self):
        if self.precisa_humano and not (self.motivo_humano or "").strip():
            raise ValueError("precisa_humano=true exige motivo_humano")
        if self.acao == Acao.escalar_humano and not self.precisa_humano:
            raise ValueError("acao escalar_humano exige precisa_humano=true")
        if self.acao not in (Acao.aguardar, Acao.escalar_humano) and not (self.mensagem_cliente or "").strip():
            raise ValueError(f"acao {self.acao.value} exige mensagem_cliente")
        return self


class ChamadoTexto(BaseModel):
    """O que o modelo escreve. Os números da evidência são preenchidos pelo código."""
    titulo: str = Field(min_length=5, max_length=140)
    hipotese_causa: str = Field(min_length=10, max_length=500)
    acao_proposta: str = Field(min_length=10, max_length=500)
    como_medir: str = Field(min_length=5, max_length=300)


class Chamado(ChamadoTexto):
    padrao_id: str
    dono: str
    evidencia: dict[str, Any]
    precisa_humano: bool = True  # H7: todo chamado passa por uma pessoa


class Resultado(BaseModel):
    order_id: str
    tipo_excecao: str
    fonte: Literal["ao_vivo", "cache", "sem_modelo"]
    decisao_modelo: Optional[Decisao] = None
    acao_final: Acao
    vai_para_humano: bool
    motivo_humano: Optional[str] = None
    regra_aplicada: Optional[str] = None
    artefato: dict[str, Any] = Field(default_factory=dict)
    ficha: dict[str, Any]
    rastro: list[dict[str, Any]] = Field(default_factory=list)
    versao_prompt: int
    modelo: Optional[str] = None  # None em decisões antigas = openai/gpt-oss-120b
    erro: Optional[str] = None
