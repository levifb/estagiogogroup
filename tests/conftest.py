"""Os CSVs do desafio não vão para o repositório (o enunciado pede para não compartilhá-los).
Sem eles em dados/operacoes/, os testes que leem dados reais são pulados com aviso; os de lógica rodam sempre."""

from pathlib import Path

import pytest

TEM_DADOS = (Path(__file__).resolve().parents[1] / "dados" / "operacoes" / "pedidos_excecao.csv").exists()

PRECISAM_DE_DADOS = {
    "test_dados.py",
    "test_negocio.py::test_otimo_nunca_perde_para_fifo_no_estoque_real",
    "test_agente.py::test_ficha_tem_os_campos_que_o_prompt_cita",
    "test_agente.py::test_modo_demo_sem_cache_nao_quebra",
}


def pytest_collection_modifyitems(config, items):
    if TEM_DADOS:
        return
    pular = pytest.mark.skip(reason="sem os CSVs do desafio em dados/operacoes/")
    for item in items:
        arquivo = Path(item.fspath).name
        if arquivo in PRECISAM_DE_DADOS or f"{arquivo}::{item.name}" in PRECISAM_DE_DADOS:
            item.add_marker(pular)
