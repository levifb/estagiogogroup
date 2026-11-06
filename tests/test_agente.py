"""Regras de humano no loop, esquema da decisão e pipeline sem rede."""

import copy

import pytest
from pydantic import ValidationError

from src.agente import regras
from src.agente.esquemas import Acao, Decisao
from src.agente.ficha import fila_do_dia, montar_ficha
from src.agente.pipeline import carregar_prompt, processar

FICHA = {
    "pedido": {"valor_pago": 100.0},
    "excecao": {"tipo": "avaria_transporte", "status": "aberta", "status_incoerente_com_tipo": False},
    "entrega": {"entregue": True, "data_entrega": "10/09/2026", "dias_uteis_atraso_vs_prometido": 3, "dias_entre_recebimento_e_reclamacao": 1},
    "cliente": {"alto_valor_acima_1500": False},
    "custos_acoes": {"reenviar": 40.0, "refazer_personalizacao": 40.0},
}


def ficha(**mudancas):
    f = copy.deepcopy(FICHA)
    for caminho, valor in mudancas.items():
        secao, campo = caminho.split("__")
        f[secao][campo] = valor
    return f


def dec(acao="reenviar", confianca="alta", precisa_humano=False, motivo=None, msg="Olá! Vamos reenviar. Mande uma foto do produto. Equipe X"):
    return Decisao(acao=acao, justificativa="justificativa de teste com dados", mensagem_cliente=msg,
                   confianca=confianca, precisa_humano=precisa_humano, motivo_humano=motivo)


def test_caso_comum_nao_vai_para_humano():
    assert regras.regra_humano(ficha(), dec()) is None


def test_h1_status_incoerente():
    assert regras.regra_humano(ficha(excecao__status_incoerente_com_tipo=True), dec())[0] == "H1"


def test_h1_registro_contraditorio():
    assert regras.regra_humano(ficha(entrega__data_entrega=None), dec())[0] == "H1"
    assert regras.regra_humano(ficha(excecao__tipo="extravio"), dec())[0] == "H1"  # extravio marcado como entregue
    assert regras.regra_humano(ficha(excecao__tipo="extravio", entrega__entregue=False, entrega__data_entrega=None), dec()) is None


def test_h2_reembolso_acima_do_limite():
    assert regras.regra_humano(ficha(pedido__valor_pago=228.01), dec("reembolsar"))[0] == "H2"
    assert regras.regra_humano(ficha(pedido__valor_pago=228.00), dec("reembolsar")) is None


def test_h3_reembolso_para_cliente_alto_valor():
    assert regras.regra_humano(ficha(cliente__alto_valor_acima_1500=True), dec("reembolsar"))[0] == "H3"
    assert regras.regra_humano(ficha(cliente__alto_valor_acima_1500=True), dec("reenviar")) is None


def test_h4_atraso_sem_entrega_acima_de_10_dias():
    f = ficha(excecao__tipo="atraso_entrega", entrega__entregue=False, entrega__dias_uteis_atraso_vs_prometido=11)
    assert regras.regra_humano(f, dec("acionar_transportadora"))[0] == "H4"
    f["entrega"]["dias_uteis_atraso_vs_prometido"] = 10
    assert regras.regra_humano(f, dec("acionar_transportadora")) is None


def test_h5_reclamacao_fora_dos_7_dias():
    assert regras.regra_humano(ficha(entrega__dias_entre_recebimento_e_reclamacao=8), dec())[0] == "H5"
    assert regras.regra_humano(ficha(entrega__dias_entre_recebimento_e_reclamacao=7), dec()) is None


def test_h6_confianca_baixa_ou_sem_decisao():
    assert regras.regra_humano(ficha(), dec(confianca="baixa"))[0] == "H6"
    assert regras.regra_humano(ficha(), None)[0] == "H6"
    assert regras.regra_humano(ficha(), dec("escalar_humano", precisa_humano=True, motivo="dúvida", msg=None))[0] == "H6"


def test_esquema_exige_motivo_e_mensagem():
    with pytest.raises(ValidationError):
        dec(precisa_humano=True, motivo=None)
    with pytest.raises(ValidationError):
        dec(acao="reenviar", msg=None)
    with pytest.raises(ValidationError):
        Decisao.model_validate_json('{"acao": "inventada", "justificativa": "xxxxxxxxxx", "confianca": "alta", "precisa_humano": false}')


def test_ficha_tem_os_campos_que_o_prompt_cita():
    f = montar_ficha(fila_do_dia()[0])
    for chave in ("dentro_do_sla_contratado", "prazo_correto_pelo_sla_dias_uteis", "dias_uteis_atraso_vs_prometido"):
        assert chave in f["entrega"]
    assert "padrao_causa_raiz" in f


def test_modo_demo_sem_cache_nao_quebra():
    versao, exemplos, _ = carregar_prompt("decisao")
    r = processar(exemplos[0], modo="demo")  # exemplos do prompt nunca são processados em lote
    assert r.vai_para_humano and r.fonte in ("sem_modelo", "cache")


def test_h2b_reenvio_acima_do_limite():
    assert regras.regra_humano(ficha(custos_acoes__reenviar=73.22), dec())[0] == "H2b"
    assert regras.regra_humano(ficha(custos_acoes__reenviar=73.21), dec()) is None


def test_h7_reenvio_sem_pedir_foto():
    sem_foto = "Olá! Vamos reenviar sem custo. Equipe X"
    nega_foto = "Olá! Vamos reenviar. Você não precisa enviar foto. Equipe X"  # caso real GB7000254
    assert regras.regra_humano(ficha(), dec(msg=sem_foto))[0] == "H7"
    assert regras.regra_humano(ficha(), dec(msg=nega_foto))[0] == "H7"
    assert regras.regra_humano(ficha(), dec()) is None
    f = ficha(excecao__tipo="extravio", entrega__entregue=False, entrega__data_entrega=None)
    assert regras.regra_humano(f, dec(msg=sem_foto)) is None  # extravio não exige foto
