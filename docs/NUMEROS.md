# Números do projeto

Gerado por `python -m analises.gerar_numeros`. Não edite à mão: mude o script e rode de novo.
Todo número que aparece no README, na interface ou no LOG é citado pelo id desta tabela.

| id | número | definição | script | gerado em |
|---|---|---|---|---|
| N01 | 2.000 | exceções abertas únicas em 30/09/2026 (pedidos_excecao.csv sem duplicata order_id+tipo_excecao) | `analises/a01_perfil.py` | 2026-11-05 |
| N02 | 2.042 | linhas no arquivo pedidos_excecao.csv, antes da limpeza | `analises/a01_perfil.py` | 2026-11-05 |
| N03 | 42 | linhas duplicadas (mesmo order_id e tipo_excecao, status diferente) removidas | `analises/a01_perfil.py` | 2026-11-05 |
| N04 | 32 | exceções pagamento_pendente com status aguardando_transportadora (incoerente), marcadas | `analises/a01_perfil.py` | 2026-11-05 |
| N05 | 13,3 | dias para zerar a fila na capacidade de 150 tratativas/dia, sem novas entradas (N01 / 150) | `analises/a01_perfil.py` | 2026-11-05 |
| N06 | 33 | exceções abertas por dia, em média, de 02/08 a 30/09/2026 (60 dias) | `analises/a01_perfil.py` | 2026-11-05 |
| N07 | 42 | exceções abertas por dia, média dos 14 dias antes de 30/09/2026 | `analises/a01_perfil.py` | 2026-11-05 |
| N08 | 198 | exceções abertas em 30/09/2026, a data de referência | `analises/a01_perfil.py` | 2026-11-05 |
| N09 | 20 dias | idade mediana das exceções abertas (30/09/2026 menos data_abertura_excecao) | `analises/a01_perfil.py` | 2026-11-05 |
| N10 | 33% | exceções abertas há mais de 30 dias | `analises/a01_perfil.py` | 2026-11-05 |
| N11 | R$ 220.161 | valor pago somado dos pedidos com exceção aberta | `analises/a01_perfil.py` | 2026-11-05 |
| N12 | R$ 98 | valor mediano de um pedido com exceção | `analises/a01_perfil.py` | 2026-11-05 |
| N13 | R$ 228 | percentil 95 do valor do pedido com exceção | `analises/a01_perfil.py` | 2026-11-05 |
| N14 | 177 | exceções de clientes com receita acumulada acima de R$ 1.500 (recompram em 70% dos casos) | `analises/a01_perfil.py` | 2026-11-05 |
| N15 | 35% | exceções paradas aguardando transportadora ou cliente | `analises/a01_perfil.py` | 2026-11-05 |
| N20 | 100% | exceções em que data_prometida = data_pedido + 1 + SLA em dias CORRIDOS (parametros.md manda dias úteis) | `analises/a02_prazo_prometido.py` | 2026-11-05 |
| N21 | 2 dias | mediana de quantos dias corridos a data prometida ao cliente vem antes do prazo correto | `analises/a02_prazo_prometido.py` | 2026-11-05 |
| N22 | 147 | exceções atraso_entrega que estão dentro do SLA contratado em dias úteis (de 497) | `analises/a02_prazo_prometido.py` | 2026-11-05 |
| N23 | 30% | parcela das exceções atraso_entrega que só existem porque o prazo prometido foi calculado em dias corridos | `analises/a02_prazo_prometido.py` | 2026-11-05 |
| N30 | 6 | padrões de causa raiz detectados (mín. 20 casos, taxa ≥ 2.5× a base, recorte mais específico) | `analises/a03_padroes.py` | 2026-11-05 |
| N31 | 914 | exceções explicadas por algum padrão de causa raiz | `analises/a03_padroes.py` | 2026-11-05 |
| N32 | 46% | parcela das exceções abertas explicada pelos padrões (N31 / N01) | `analises/a03_padroes.py` | 2026-11-05 |
| N33 | R$ 101.830 | valor pago dos pedidos explicados pelos padrões | `analises/a03_padroes.py` | 2026-11-05 |
| N40 | 396 | P01 transportadora+regiao=Rota Express / Nordeste (atraso_entrega, rastreio_parado): 396 de 477 exceções do grupo (83% contra 18% nos demais, 4.7×); R$ 44.164 | `analises/a03_padroes.py` | 2026-11-05 |
| N41 | 210 | P02 cd+turno=CD2 / noite (item_faltante): 210 de 456 exceções do grupo (46% contra 4% nos demais, 10.5×); R$ 21.476 | `analises/a03_padroes.py` | 2026-11-05 |
| N42 | 98 | P03 transportadora=Carga Norte (avaria_transporte): 98 de 340 exceções do grupo (29% contra 5% nos demais, 5.4×); R$ 13.907 | `analises/a03_padroes.py` | 2026-11-05 |
| N43 | 74 | P04 sku+lote=APC-1067 / L2607-B (vazamento_produto): 74 de 75 exceções do grupo (99% contra 2% nos demais, 51.3×); R$ 8.361 | `analises/a03_padroes.py` | 2026-11-05 |
| N44 | 77 | P05 maquina=IMP-02 (falha_personalizacao): 77 de 162 exceções do grupo (48% contra 11% nos demais, 4.4×); R$ 9.689 | `analises/a03_padroes.py` | 2026-11-05 |
| N45 | 59 | P06 marca=Kokeshi (ruptura_pos_venda): 59 de 257 exceções do grupo (23% contra 4% nos demais, 6.5×); R$ 4.233 | `analises/a03_padroes.py` | 2026-11-05 |
| N50 | 24/08/2026 | semana (data do pedido) em que as falhas de personalização da IMP-02 passam a 5 ou mais por semana | `analises/a03_padroes.py` | 2026-11-05 |
| N51 | 7 | falhas de personalização da IMP-02 antes dessa semana | `analises/a03_padroes.py` | 2026-11-05 |
| N52 | 75% | pedidos com brinde entre os itens faltantes do CD2 no turno da noite | `analises/a03_padroes.py` | 2026-11-05 |
| N53 | 36% | pedidos com brinde entre todas as exceções (base de comparação para N52) | `analises/a03_padroes.py` | 2026-11-05 |
| N54 | 3,0 | dias úteis médios além do SLA contratado nas entregas da Rota Express no Nordeste | `analises/a03_padroes.py` | 2026-11-05 |
| N55 | 0,8 | dias úteis médios além do SLA contratado nas demais entregas (base de comparação para N54) | `analises/a03_padroes.py` | 2026-11-05 |
