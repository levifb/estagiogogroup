"""Camada de dados: limpeza contada, junções completas e padrões detectados."""

import subprocess

from src.dados.base import base_trabalho, relatorio_limpeza
from src.dados.padroes import detectar


def test_limpeza_remove_duplicatas_e_conta():
    df = base_trabalho()
    assert not df.duplicated(["order_id", "tipo_excecao"]).any()
    regras = {r.regra[:2]: r for r in relatorio_limpeza()}
    assert regras["R1"].efeito == "removida" and regras["R1"].linhas_afetadas > 0
    assert regras["R2"].efeito == "marcada"
    assert df["status_incoerente"].sum() == regras["R2"].linhas_afetadas


def test_juncoes_completas():
    df = base_trabalho()
    assert df["sla_contratado_dias_uteis"].notna().all(), "toda exceção precisa achar o SLA da transportadora na UF"
    assert df["receita_acumulada"].notna().all(), "todo cliente precisa estar em clientes.csv"


def test_atraso_sla_nunca_maior_que_atraso_prometido():
    # O prazo correto (dias úteis) é sempre igual ou posterior ao prometido (dias corridos).
    df = base_trabalho()
    assert (df["prazo_correto"] >= df["data_prometida"]).all()
    assert (df["atraso_du_sla"] <= df["atraso_du_prometido"]).all()


def test_padroes_tem_base_e_nao_se_sobrepoem():
    ps = detectar(base_trabalho())
    assert ps, "esperado pelo menos um padrão"
    vistos = set()
    for p in ps:
        assert p.taxa_grupo > p.taxa_base
        assert p.casos == len(p.order_ids)
        sobreposicao = vistos & set(p.order_ids)
        assert len(sobreposicao) <= 0.5 * p.casos
        vistos |= set(p.order_ids)


def test_so_a_fonte_le_csv():
    saida = subprocess.run(["git", "grep", "--untracked", "-l", "read_csv", "--", "src", "api", "eval"],
                           capture_output=True, text=True).stdout.split()
    assert saida in ([], ["src/dados/fonte.py"]), saida
