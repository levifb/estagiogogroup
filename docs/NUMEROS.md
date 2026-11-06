# Números do projeto

Gerado por `python -m analises.gerar_numeros`. Não edite à mão: mude o script e rode de novo.
Todo número que aparece no README, na interface ou no LOG é citado pelo id desta tabela.

| id | número | definição | script | gerado em |
|---|---|---|---|---|
| N01 | 2.000 | exceções abertas únicas em 30/09/2026 (pedidos_excecao.csv sem duplicata order_id+tipo_excecao) | `analises/a01_perfil.py` | 2026-11-06 |
| N02 | 2.042 | linhas no arquivo pedidos_excecao.csv, antes da limpeza | `analises/a01_perfil.py` | 2026-11-06 |
| N03 | 42 | linhas duplicadas (mesmo order_id e tipo_excecao, status diferente) removidas | `analises/a01_perfil.py` | 2026-11-06 |
| N04 | 32 | exceções pagamento_pendente com status aguardando_transportadora (incoerente), marcadas | `analises/a01_perfil.py` | 2026-11-06 |
| N05 | 13,3 | dias para zerar a fila na capacidade de 150 tratativas/dia, sem novas entradas (N01 / 150) | `analises/a01_perfil.py` | 2026-11-06 |
| N06 | 33 | exceções abertas por dia, em média, de 02/08 a 30/09/2026 (60 dias) | `analises/a01_perfil.py` | 2026-11-06 |
| N07 | 42 | exceções abertas por dia, média dos 14 dias antes de 30/09/2026 | `analises/a01_perfil.py` | 2026-11-06 |
| N08 | 198 | exceções abertas em 30/09/2026, a data de referência | `analises/a01_perfil.py` | 2026-11-06 |
| N09 | 20 dias | idade mediana das exceções abertas (30/09/2026 menos data_abertura_excecao) | `analises/a01_perfil.py` | 2026-11-06 |
| N10 | 33% | exceções abertas há mais de 30 dias | `analises/a01_perfil.py` | 2026-11-06 |
| N11 | R$ 220.161 | valor pago somado dos pedidos com exceção aberta | `analises/a01_perfil.py` | 2026-11-06 |
| N12 | R$ 98 | valor mediano de um pedido com exceção | `analises/a01_perfil.py` | 2026-11-06 |
| N13 | R$ 228 | percentil 95 do valor do pedido com exceção | `analises/a01_perfil.py` | 2026-11-06 |
| N14 | 177 | exceções de clientes com receita acumulada acima de R$ 1.500 (recompram em 70% dos casos) | `analises/a01_perfil.py` | 2026-11-06 |
| N15 | 35% | exceções paradas aguardando transportadora ou cliente | `analises/a01_perfil.py` | 2026-11-06 |
| N20 | 100% | exceções em que data_prometida = data_pedido + 1 + SLA em dias CORRIDOS (parametros.md manda dias úteis) | `analises/a02_prazo_prometido.py` | 2026-11-06 |
| N21 | 2 dias | mediana de quantos dias corridos a data prometida ao cliente vem antes do prazo correto | `analises/a02_prazo_prometido.py` | 2026-11-06 |
| N22 | 147 | exceções atraso_entrega que estão dentro do SLA contratado em dias úteis (de 497) | `analises/a02_prazo_prometido.py` | 2026-11-06 |
| N23 | 30% | parcela das exceções atraso_entrega que só existem porque o prazo prometido foi calculado em dias corridos | `analises/a02_prazo_prometido.py` | 2026-11-06 |
| N30 | 6 | padrões de causa raiz detectados (mín. 20 casos, taxa ≥ 2.5× a base, recorte mais específico) | `analises/a03_padroes.py` | 2026-11-06 |
| N31 | 914 | exceções explicadas por algum padrão de causa raiz | `analises/a03_padroes.py` | 2026-11-06 |
| N32 | 46% | parcela das exceções abertas explicada pelos padrões (N31 / N01) | `analises/a03_padroes.py` | 2026-11-06 |
| N33 | R$ 101.830 | valor pago dos pedidos explicados pelos padrões | `analises/a03_padroes.py` | 2026-11-06 |
| N40 | 396 | P01 transportadora+regiao=Rota Express / Nordeste (atraso_entrega, rastreio_parado): 396 de 477 exceções do grupo (83% contra 18% nos demais, 4.7×); R$ 44.164 | `analises/a03_padroes.py` | 2026-11-06 |
| N41 | 210 | P02 cd+turno=CD2 / noite (item_faltante): 210 de 456 exceções do grupo (46% contra 4% nos demais, 10.5×); R$ 21.476 | `analises/a03_padroes.py` | 2026-11-06 |
| N42 | 98 | P03 transportadora=Carga Norte (avaria_transporte): 98 de 340 exceções do grupo (29% contra 5% nos demais, 5.4×); R$ 13.907 | `analises/a03_padroes.py` | 2026-11-06 |
| N43 | 74 | P04 sku+lote=APC-1067 / L2607-B (vazamento_produto): 74 de 75 exceções do grupo (99% contra 2% nos demais, 51.3×); R$ 8.361 | `analises/a03_padroes.py` | 2026-11-06 |
| N44 | 77 | P05 maquina=IMP-02 (falha_personalizacao): 77 de 162 exceções do grupo (48% contra 11% nos demais, 4.4×); R$ 9.689 | `analises/a03_padroes.py` | 2026-11-06 |
| N45 | 59 | P06 marca=Kokeshi (ruptura_pos_venda): 59 de 257 exceções do grupo (23% contra 4% nos demais, 6.5×); R$ 4.233 | `analises/a03_padroes.py` | 2026-11-06 |
| N50 | 24/08/2026 | semana (data do pedido) em que as falhas de personalização da IMP-02 passam a 5 ou mais por semana | `analises/a03_padroes.py` | 2026-11-06 |
| N51 | 7 | falhas de personalização da IMP-02 antes dessa semana | `analises/a03_padroes.py` | 2026-11-06 |
| N52 | 75% | pedidos com brinde entre os itens faltantes do CD2 no turno da noite | `analises/a03_padroes.py` | 2026-11-06 |
| N53 | 36% | pedidos com brinde entre todas as exceções (base de comparação para N52) | `analises/a03_padroes.py` | 2026-11-06 |
| N54 | 3,0 | dias úteis médios além do SLA contratado nas entregas da Rota Express no Nordeste | `analises/a03_padroes.py` | 2026-11-06 |
| N55 | 0,8 | dias úteis médios além do SLA contratado nas demais entregas (base de comparação para N54) | `analises/a03_padroes.py` | 2026-11-06 |
| N60 | R$ 94.009 | perda esperada se todas as 2.000 exceções fossem tratadas hoje = reembolso esperado + recompra perdida + custo de resolução (SPEC.md S1–S6) **(estimativa)** | `analises/a04_valor_em_risco.py` | 2026-11-06 |
| N61 | R$ 56.285 | reembolso esperado hoje: soma de P(cancelamento pelos dias úteis de atraso contra o prometido) × valor pago **(estimativa)** | `analises/a04_valor_em_risco.py` | 2026-11-06 |
| N62 | R$ 11.556 | recompra perdida hoje: soma de P(cancelamento) × P(recompra 70% ou 28%) × 0,5 × ticket médio do cliente **(estimativa)** | `analises/a04_valor_em_risco.py` | 2026-11-06 |
| N63 | R$ 26.168 | custo de resolução hoje: soma de (1 − P(cancelamento)) × custo da ação padrão (reenvio = 24% do valor + frete) **(estimativa)** | `analises/a04_valor_em_risco.py` | 2026-11-06 |
| N64 | 163 | exceções cuja perda esperada sobe se esperarem 1 dia útil (estão num degrau da tabela de cancelamento) | `analises/a04_valor_em_risco.py` | 2026-11-06 |
| N65 | R$ 1.552 | quanto a perda esperada total sobe se nenhuma exceção for tratada amanhã (1 dia útil a mais) **(estimativa)** | `analises/a04_valor_em_risco.py` | 2026-11-06 |
| N66 | R$ 10.416 | quanto a perda esperada total sobe se nenhuma exceção for tratada por 5 dias úteis **(estimativa)** | `analises/a04_valor_em_risco.py` | 2026-11-06 |
| N68 | R$ 73 | percentil 95 do custo de reenvio (24% do valor + frete médio) nas 2.000 exceções; acima disso o reenvio vai para a analista (regra H2b) | `analises/a04_valor_em_risco.py` | 2026-11-06 |
| N67 | 234 | atrasos já entregues: o atraso parou de crescer, então tratar hoje ou depois não muda o risco | `analises/a04_valor_em_risco.py` | 2026-11-06 |
| N70 | R$ 112.698 | perda esperada tratando o estoque em ordem de chegada, 150/dia útil (processo atual) **(estimativa)** | `analises/a05_simulacao.py` | 2026-11-06 |
| N71 | R$ 95.249 | perda esperada com o plano otimizado (atribuição exata casos × dias), 150/dia útil **(estimativa)** | `analises/a05_simulacao.py` | 2026-11-06 |
| N72 | R$ 17.448 | perda evitada pelo plano otimizado em relação à ordem de chegada (N70 − N71) **(estimativa)** | `analises/a05_simulacao.py` | 2026-11-06 |
| N73 | 15% | redução da perda esperada em relação à ordem de chegada **(estimativa)** | `analises/a05_simulacao.py` | 2026-11-06 |
| N74 | 93% | parcela da perda evitável capturada pelo plano otimizado: (N70 − N71) / (N70 − N60); N60 seria tratar tudo hoje, o que não é possível **(estimativa)** | `analises/a05_simulacao.py` | 2026-11-06 |
| N75 | R$ 101.908 | perda esperada priorizando o maior valor de pedido (comparação) **(estimativa)** | `analises/a05_simulacao.py` | 2026-11-06 |
| N76 | R$ 108.322 | perda esperada priorizando a maior perda atual (comparação) **(estimativa)** | `analises/a05_simulacao.py` | 2026-11-06 |
| N80 | 161 | P01 (Rota Express / Nordeste): exceções por mês acima da taxa de base = excesso 311 × 30/58 dias **(estimativa)** | `analises/a05_simulacao.py` | 2026-11-06 |
| N81 | R$ 4.564 | P01 (Rota Express / Nordeste): perda evitável por mês = exceções/mês acima da base × perda esperada média do padrão hoje (R$ 28) **(estimativa)** | `analises/a05_simulacao.py` | 2026-11-06 |
| N82 | 98 | P02 (CD2 / noite): exceções por mês acima da taxa de base = excesso 190 × 30/58 dias **(estimativa)** | `analises/a05_simulacao.py` | 2026-11-06 |
| N83 | R$ 6.774 | P02 (CD2 / noite): perda evitável por mês = exceções/mês acima da base × perda esperada média do padrão hoje (R$ 69) **(estimativa)** | `analises/a05_simulacao.py` | 2026-11-06 |
| N84 | 41 | P03 (Carga Norte): exceções por mês acima da taxa de base = excesso 80 × 30/58 dias **(estimativa)** | `analises/a05_simulacao.py` | 2026-11-06 |
| N85 | R$ 3.599 | P03 (Carga Norte): perda evitável por mês = exceções/mês acima da base × perda esperada média do padrão hoje (R$ 87) **(estimativa)** | `analises/a05_simulacao.py` | 2026-11-06 |
| N86 | 38 | P04 (APC-1067 / L2607-B): exceções por mês acima da taxa de base = excesso 73 × 30/58 dias **(estimativa)** | `analises/a05_simulacao.py` | 2026-11-06 |
| N87 | R$ 2.649 | P04 (APC-1067 / L2607-B): perda evitável por mês = exceções/mês acima da base × perda esperada média do padrão hoje (R$ 71) **(estimativa)** | `analises/a05_simulacao.py` | 2026-11-06 |
| N88 | 31 | P05 (IMP-02): exceções por mês acima da taxa de base = excesso 60 × 30/58 dias **(estimativa)** | `analises/a05_simulacao.py` | 2026-11-06 |
| N89 | R$ 2.224 | P05 (IMP-02): perda evitável por mês = exceções/mês acima da base × perda esperada média do padrão hoje (R$ 72) **(estimativa)** | `analises/a05_simulacao.py` | 2026-11-06 |
| N90 | 26 | P06 (Kokeshi): exceções por mês acima da taxa de base = excesso 50 × 30/58 dias **(estimativa)** | `analises/a05_simulacao.py` | 2026-11-06 |
| N91 | R$ 745 | P06 (Kokeshi): perda evitável por mês = exceções/mês acima da base × perda esperada média do padrão hoje (R$ 29) **(estimativa)** | `analises/a05_simulacao.py` | 2026-11-06 |
| N95 | 76 | atrasos por mês que somem ao calcular o prazo prometido em dias úteis = N22 × 30/58 dias **(estimativa)** | `analises/a05_simulacao.py` | 2026-11-06 |
| N96 | R$ 389 | perda esperada por mês desses atrasos (perda média hoje R$ 5) **(estimativa)** | `analises/a05_simulacao.py` | 2026-11-06 |
| N97 | 430 | exceções por mês evitáveis mudando o processo: (excesso dos padrões 763 + 68 atrasos falsos fora dos padrões) × 30/58 **(estimativa)** | `analises/a05_simulacao.py` | 2026-11-06 |
| N98 | 86 h | horas do time por mês liberadas por N97, a 12 minutos por tratativa (parametros.md) **(estimativa)** | `analises/a05_simulacao.py` | 2026-11-06 |
| N100 | 150 | casos da fila do dia com decisão do modelo (de 150); por modelo: gpt-oss-120b: 76, gpt-oss-20b: 74 | `analises/a06_fila_do_dia.py` | 2026-11-06 |
| N101 | 144 | decisões da fila do dia que batem com a tabela de política do SPEC (checagem automática) | `analises/a06_fila_do_dia.py` | 2026-11-06 |
| N102 | 8 | casos da fila do dia enviados à analista pelas regras H1–H7 | `analises/a06_fila_do_dia.py` | 2026-11-06 |
| N103 | 147 | mensagens ao cliente da fila do dia sem problema nas checagens automáticas (de 149) | `analises/a06_fila_do_dia.py` | 2026-11-06 |
