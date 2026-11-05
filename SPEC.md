# SPEC: Mesa de exceções

Os números entre colchetes, como [N01], são ids de `docs/NUMEROS.md`, onde estão o valor, a definição e o script que gera cada um. Os dados são os sintéticos do desafio, com data de referência 30/09/2026.

## Persona

Marina, analista de exceções de operações do Gogroup (nome fictício). Ela recebe a fila de pedidos que saíram do fluxo normal (atraso, extravio, avaria, falha de personalização, pagamento pendente, ruptura, endereço divergente e outros) e decide o que fazer com cada um. O time dela dá conta de 150 tratativas por dia, de 12 minutos cada.

## Dor

- Há 2.000 exceções abertas [N01]. Na capacidade atual, são 13,3 dias de fila [N05].
- A fila é tratada por ordem de chegada. Um pedido que vai cruzar uma faixa de risco de cancelamento amanhã espera atrás de outro que não muda nada se esperar uma semana.
- A perda esperada do estoque atual, tratado em ordem de chegada, é de R$ 118.043 [N70] em reembolsos, recompras perdidas e custos de reenvio (estimativa).
- 46% das exceções [N32] vêm de 6 causas de processo que se repetem [N30]: uma impressora, um turno de um CD, um lote, duas transportadoras e uma marca. Tratar caso a caso não faz essas causas pararem.
- 30% dos "atrasos" [N23] não são atrasos da transportadora. O checkout calcula a data prometida em dias corridos [N20], enquanto o SLA contratado é em dias úteis.

## Fluxo atual

1. A exceção é aberta e entra no fim da fila.
2. A analista pega o próximo caso por ordem de chegada, consulta pedido, cliente e transportadora em telas diferentes e decide a ação.
3. Escreve a mensagem ao cliente e aciona a transportadora ou o reenvio.
4. Ninguém olha a fila como um todo, então padrões como "a IMP-02 começou a falhar em 24/08" [N50] só aparecem quando alguém repara.

## Fluxo novo

1. Priorização, feita pelo código, sem IA. Todo dia o sistema calcula a perda esperada de cada caso em cada dia futuro e escolhe os 150 de hoje com um plano ótimo para o horizonte inteiro (ver "Priorização").
2. Agente de decisão, com IA. Para cada caso da fila do dia, o agente lê a ficha (pedido, cliente, prazos, atraso em dias úteis, risco, padrão a que pertence), consulta ferramentas quando precisa e propõe ação, justificativa e mensagem ao cliente, em JSON validado.
3. Regras em código. O que é caro, sensível ou incerto vai para a Marina, com o motivo. O sistema executa o resto de forma simulada: manda a mensagem, abre o reenvio, aciona a transportadora.
4. Investigador de causa raiz. O código detecta os padrões e a IA redige um chamado para o dono do processo, com a evidência. A Marina aprova antes do envio.
5. A Marina passa o dia na fila de aprovação e nos chamados. Juntar pedido, cliente e transportadora numa ficha fica com o sistema.

## Métricas

**De processo**
- Acerto do agente no gabarito, por etapa: ação, decisão de mandar para o humano e padrão (eval).
- Recall de "deve ir para o humano": caso de risco tratado sozinho é o erro mais caro.
- Parcela da fila do dia resolvida sem intervenção, e motivos de escalonamento.
- Tempo e tokens por caso.

**De negócio**
- Perda esperada evitada pela priorização: R$ 18.175 [N72], ou 15% [N73] em relação à ordem de chegada (estimativa).
- Exceções por mês evitáveis mudando processos: 430 [N97], ou 86 horas do time por mês [N98] (estimativa).

## Priorização

O custo de um caso depende do dia em que ele é tratado. A tabela de cancelamento do `parametros.md` é em degraus: até 2 dias úteis de atraso, 4%; de 3 a 5, 10%; de 6 a 10, 22%; mais de 10, 40%. Um caso com 2 dias de atraso que espera até amanhã sobe de 4% para 10%. Um caso que já passou de 10 dias está no teto e não piora mais.

Por isso a pergunta que ordena a fila é **quanto cada caso piora se esperar**. O risco de hoje engana: o caso no teto parece o mais grave e é justamente o que pode esperar. Como toda tratativa leva os mesmos 12 minutos, cada dia vira 150 vagas iguais, e escolher o dia de cada caso minimizando a perda total é um **problema de atribuição** (casos × vagas). O algoritmo húngaro resolve esse problema de forma exata (`scipy.optimize.linear_sum_assignment`), em poucos segundos para 2.000 casos.

Eu comecei pensando num guloso que olha só o dia seguinte, e ele não basta: um caso com 1 dia de atraso não piora amanhã, mas salta no dia seguinte. A atribuição enxerga o horizonte todo, e há um teste com esse exemplo em `tests/test_negocio.py`.

Comparação no estoque de 30/09 (estimativas):

| Política | Perda esperada |
|---|---|
| Ordem de chegada (atual) | R$ 118.043 [N70] |
| Maior perda hoje primeiro | R$ 113.985 [N76] |
| Maior valor de pedido primeiro | R$ 106.856 [N75] |
| **Plano otimizado** | **R$ 99.868** [N71] |
| Piso teórico (tratar tudo hoje, impossível) | R$ 98.462 [N60] |

O plano otimizado captura 93% [N74] da perda que dá para evitar.

## Modelo de perda esperada

Para um caso tratado no dia útil `t` (t = 0 é 30/09/2026), com P = probabilidade de cancelamento pela tabela, usando os dias úteis de atraso em relação ao prazo prometido no dia `t`:

- **reembolso esperado** = P × valor pago;
- **recompra perdida** = P × P(recompra) × 0,5 × ticket médio do cliente, com P(recompra) de 70% para receita acumulada acima de R$ 1.500 e 28% nos demais casos (estimativa);
- **custo de resolução** = (1 − P) × custo da ação padrão. Quem cancela é reembolsado e não recebe reenvio, para não contar duas vezes.

Custos (`parametros.md`): reenvio = 24% do valor (CMV) + frete médio da transportadora; refazer personalização = custo de reenvio; reembolso = valor pago.

## Política de ações

Ações: `reenviar`, `refazer_personalizacao`, `reembolsar`, `acionar_transportadora`, `contatar_cliente`, `aguardar`, `escalar_humano`. Toda ação, exceto `aguardar` e `escalar_humano`, leva mensagem ao cliente.

### Ação por tipo de exceção

| Tipo | Situação | Ação padrão | Também aceitável |
|---|---|---|---|
| atraso_entrega | já entregue | contatar_cliente (pedido de desculpas, sem custo) | — |
| atraso_entrega | não entregue, **dentro do SLA contratado** (só passou da data prometida) | contatar_cliente com o prazo correto | — |
| atraso_entrega | não entregue, fora do SLA, até 10 dias úteis de atraso | acionar_transportadora | contatar_cliente |
| atraso_entrega | não entregue, mais de 10 dias úteis de atraso | escalar_humano (S8) | — |
| rastreio_parado | qualquer | acionar_transportadora | — |
| extravio | qualquer | reenviar | acionar_transportadora |
| devolvido_transportadora | qualquer | reenviar, confirmando o endereço na mensagem | contatar_cliente |
| avaria_transporte, vazamento_produto, item_faltante | reclamação em até 7 dias do recebimento | reenviar, pedindo foto | — |
| avaria_transporte, vazamento_produto, item_faltante | depois de 7 dias | escalar_humano (fora da política) | — |
| falha_personalizacao | qualquer | refazer_personalizacao, pedindo foto | — |
| pagamento_pendente | qualquer | contatar_cliente | — |
| endereco_divergente | qualquer | contatar_cliente para confirmar o endereço | — |
| ruptura_pos_venda | qualquer | contatar_cliente oferecendo espera ou reembolso | reembolsar |

Status `aguardando_cliente`: a ação passa a ser `contatar_cliente` (lembrete), exceto quando uma regra abaixo manda para o humano.

### Humano no loop (código, `src/agente/regras.py`)

Em ordem de precedência, a primeira regra que se aplica decide:

| Regra | Condição | Por quê |
|---|---|---|
| H1 | status incoerente com o tipo (ex.: pagamento pendente aguardando transportadora) [N04] | o registro está errado; agir em cima dele pode piorar |
| H2 | ação `reembolsar` com valor acima de R$ 228 [N13] | os 5% de pedidos mais caros; reembolso é dinheiro que não volta |
| H3 | ação `reembolsar` para cliente com receita acumulada acima de R$ 1.500 | o cliente que recompra em 70% dos casos merece uma pessoa |
| H4 | atraso não entregue com mais de 10 dias úteis | risco no teto (40%); escolher entre reenvio e reembolso é decisão de negócio (S8) |
| H5 | avaria, vazamento ou faltante reclamados depois de 7 dias do recebimento | fora da política |
| H6 | confiança do agente `baixa`, ou JSON inválido duas vezes | o agente pediu ajuda ou falhou |
| H7 | todo chamado de causa raiz | muda processo de outra área |

O código pode transformar uma ação automática em `escalar_humano`, nunca o contrário.

## Recomendações de processo

Estimativas por mês, contando só as exceções acima da taxa de base do grupo. A perda é a perda esperada média dos casos do padrão hoje.

| Padrão | Dono | Ação proposta | Exceções/mês evitáveis | Perda/mês | Como medir em 30 dias |
|---|---|---|---|---|---|
| Prazo prometido em dias corridos [N20, N22] | TI do checkout | calcular a data prometida em dias úteis, como manda o SLA | 76 [N95] | R$ 389 [N96] | % de `atraso_entrega` dentro do SLA cai para perto de 0 |
| P01 Rota Express no Nordeste [N40, N54] | Gestão de transportadoras | cobrar o SLA, avaliar multa contratual e testar outra transportadora no Nordeste | 161 [N80] | R$ 4.564 [N81] | dias úteis além do SLA no Nordeste |
| P02 CD2, turno da noite, item faltante [N41, N52] | Supervisão do CD2 | conferência do brinde na separação noturna (75% desses pedidos têm brinde [N52], contra 36% na base [N53]) | 98 [N82] | R$ 6.774 [N83] | itens faltantes por turno |
| P03 Carga Norte, avaria [N42] | Gestão de transportadoras | revisar embalagem e manuseio com a Carga Norte | 41 [N84] | R$ 3.599 [N85] | avarias por mil envios da Carga Norte |
| P04 APC-1067 lote L2607-B, vazamento [N43] | Qualidade / fornecedor | bloquear o lote e acionar o fornecedor | 38 [N86] | R$ 2.649 [N87] | vazamentos do SKU após o bloqueio |
| P05 IMP-02, falha de personalização desde 24/08 [N44, N50] | Manutenção | manutenção da impressora; redistribuir a produção enquanto isso | 31 [N88] | R$ 2.224 [N89] | falhas por máquina por semana |
| P06 Kokeshi, ruptura pós-venda [N45] | Compras / planejamento | revisar o estoque de segurança da marca | 26 [N90] | R$ 745 [N91] | rupturas Kokeshi por semana |

## Definição do pronto

Quem abre o link público, sem login, vê a fila do dia priorizada com a decisão do agente para cada caso, os casos que foram para a Marina com o motivo e os chamados de causa raiz, e o README mostra o acerto do agente medido em gabarito e quanto a priorização evita de perda, com todos os números rastreáveis a `docs/NUMEROS.md`.

## Suposições

- **S1** O cliente com avaria, vazamento, item faltante, extravio, devolução, ruptura, pagamento pendente ou endereço divergente ainda não tem o produto em condições, então a espera dele continua contando a partir da data prometida. O atraso já entregue para de crescer. *Por quê:* a tabela de cancelamento mede a impaciência do cliente com o atraso; quem recebeu um produto quebrado está na mesma situação de quem não recebeu.
- **S2** Tratar o caso trava o atraso no dia do tratamento: o cliente é informado e a solução está em andamento. *Por quê:* sem isso, nenhuma tratativa mudaria o risco. É a hipótese que dá valor à priorização, e a primeira que eu validaria com dados reais.
- **S3** "Exceção mal resolvida" (que corta a recompra pela metade, segundo o `parametros.md`) é o cliente que cancela. *Por quê:* é o único desfecho ruim que os dados permitem medir.
- **S4** Cliente com receita acumulada acima de R$ 1.500 é tratado até o 2º dia útil. *Por quê:* recompra em 70% dos casos; são 177 exceções [N14], e caber nos três primeiros dias custa pouco ao plano.
- **S5** Na devolução pela transportadora, o produto volta ao CD, então o reenvio custa só o frete.
- **S6** Entre casos de perda igual, o mais antigo vai primeiro (desempate de centavos, que nunca troca R$ de perda por idade). *Por quê:* evita que casos no teto de risco fiquem parados para sempre.
- **S7** A simulação trata o estoque de 30/09. As exceções novas (cerca de 42 por dia [N07]) entram no replanejamento diário e afetam todas as políticas por igual. Abrem em média 33 exceções por dia [N06], bem abaixo da capacidade de 150, e mesmo assim a fila tem idade mediana de 20 dias [N09] e 35% dos casos parados aguardando transportadora ou cliente [N15]. Supomos que uma exceção precisa de várias tratativas até fechar e que parte da capacidade vai para os casos em espera. É uma boa pergunta para o time de operações.
- **S8** Atraso sem entrega acima de 10 dias úteis vai para uma pessoa: a escolha entre reenviar (custo de 24% + frete) e reembolsar é de negócio, e o risco já está no teto.
- **S9** As políticas de reenvio, refação e reembolso (foto, 7 dias do recebimento) são as do material do case Atendimento do mesmo desafio e valem também para Operações.
- **S10** Entrega depois do prazo conta pelo menos 1 dia útil de atraso, mesmo em fim de semana (`src/dados/calendario.py`).
- **S11** A "taxa" dos padrões é a proporção de um tipo de exceção entre as exceções do grupo, porque o arquivo não traz o total de pedidos por máquina, turno ou transportadora. Com dados reais, a taxa deve ser sobre todos os pedidos.
