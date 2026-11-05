# Achados iniciais (exploração de 05/11/2026)

Feitos com scripts descartáveis, fora do repositório. São **hipóteses verificadas uma vez**: antes de citar qualquer um, reproduza num script em `analises/` e registre em `docs/NUMEROS.md`. Se o número reproduzido for diferente, vale o novo; anote a divergência no LOG.md.

## Volume e qualidade

- `pedidos_excecao.csv`: 2.042 linhas, 21 colunas, sem nulos fora de `data_entrega` (1.211 vazias) e `maquina` (1.378 vazias, esperadas fora da Gocase).
- 42 linhas são duplicatas de `order_id` + `tipo_excecao` com `status` diferente. Sem elas, ficam 2.000 exceções únicas.
- 32 exceções `pagamento_pendente` estão com status `aguardando_transportadora`, combinação incoerente.
- `clientes.csv`: 1.300 clientes, junção de 100%; 121 com `receita_acumulada` > R$ 1.500 (177 exceções desses clientes).
- `transportadoras.csv`: 5 transportadoras × 22 UFs = 110 linhas; toda exceção encontra o SLA.
- Fila: 2.000 / 150 por dia = 13,3 dias de backlog.

## Prazo prometido

- Em 2.042 de 2.042 linhas, `data_prometida` = `data_pedido` + 1 + `sla_contratado_dias_uteis` em **dias corridos**. O `parametros.md` manda contar em dias úteis.
- Recalculando o prazo pela regra correta, 147 das 497 exceções `atraso_entrega` (≈30%) não estão atrasadas em relação ao SLA contratado.

## Concentrações (taxa contra base)

| Padrão | Exceções | Valor (R$) | Evidência |
|---|---|---|---|
| IMP-02, falha de personalização | 77 | 9.689 | taxa 47,5% dos pedidos Gocase da IMP-02 contra 10,8% nas demais; sobe a partir da semana de 24/08/2026 |
| CD2 turno noite, item faltante | 210 | 21.476 | 215 das 285 de item faltante (antes da deduplicação); 216 das 285 com brinde no pedido |
| SKU APC-1067 lote L2607-B, vazamento | 74 | 8.361 | 76 das 113 de vazamento antes da deduplicação |
| Rota Express no Nordeste, atraso/rastreio parado | 396 | 44.164 | entrega excede o SLA em mediana de 2 dias úteis; nas demais transportadoras/regiões, 0 |
| Carga Norte, avaria no transporte | 98 | 13.907 | 102 das 192 avarias antes da deduplicação |
| Kokeshi, ruptura pós-venda | 59 | 4.233 | 61 das 123 rupturas antes da deduplicação |

Soma sem dupla contagem: 914 de 2.000 exceções (45,7%), R$ 101.830. Nordeste = BA, PE, CE, RN, PB, MA, AL, PI, SE.

## Dinheiro em risco (primeira conta)

- 492 pedidos de `atraso_entrega`, `rastreio_parado` ou `extravio` ainda sem entrega, somando R$ 54.244. Reembolso esperado hoje (P de cancelamento pela tabela de dias úteis × valor): R$ 13.570; com mais 5 dias úteis de espera: R$ 18.106.
- Recompra em risco (estimativa): P(recompra) × 0,5 × ticket médio do cliente (receita_acumulada / n_pedidos), somado nas 2.000 exceções: R$ 42.016.
- Custo de reenvio dos tipos físicos (avaria, vazamento, faltante, personalização, extravio): 0,24 × valor + frete médio = R$ 34.649.
- Valor total das 2.000 exceções: R$ 220.161.
