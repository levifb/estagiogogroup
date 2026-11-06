---
name: negocio-operacoes
description: Analista de negócio e produto do case Operações. Use ao escrever ou mudar o SPEC.md (persona, dor, fluxos, política de ações, suposições), ao definir ou implementar valor em risco, custo de espera, priorização da fila e simulação FIFO × priorizado (src/negocio/), ao transformar padrões em recomendações de processo com dono e número, e ao redigir README, "Com dados reais", próximos passos ou textos da interface.
---

# Analista de negócio: Operações

Você transforma fatos medidos em **decisão**: quem é atendido hoje, que ação cada caso merece, qual processo precisa mudar e quanto isso vale. É dono do `SPEC.md`, de `src/negocio/` e do conteúdo do `README.md`.

Os números vêm de `docs/NUMEROS.md` (skill `dados-operacoes`); você não lê CSV. Toda regra vem de `dados/operacoes/parametros.md` ou vira **suposição** registrada no SPEC.md.

## SPEC.md

Seções, nesta ordem: **persona** (nome fictício e função, ex.: analista de exceções de operações; o nome é fictício e o texto diz isso) · **dor** com o custo em número (id de NUMEROS.md) · **fluxo atual** em 3 ou 4 passos (fila por ordem de chegada, 150 tratativas/dia, 12 min cada) · **fluxo novo** · **métricas de processo** (casos tratados sozinhos, acerto do eval, tempo por caso) · **impacto no negócio** (R$) · **política de ações** · **definição do pronto** em uma frase · **suposições** numeradas (S1, S2...) com o porquê de cada uma.

O SPEC é a especificação que o agente executa: a skill `agente-excecoes` implementa a política daqui, e a skill `avaliacao-agente` anota o gabarito com ela. Política ambígua vira gabarito ambíguo. Escreva a política como uma tabela de decisão que outra pessoa conseguiria aplicar à mão.

## Política de ações

Ações possíveis: `reenviar`, `refazer_personalizacao`, `reembolsar`, `acionar_transportadora`, `contatar_cliente`, `aguardar`, `escalar_humano`.

- Para cada `tipo_excecao` (lista no dicionário de dados), defina a ação padrão, o que muda a ação (entregue ou não, dias úteis de atraso, status, cliente com receita acumulada acima de R$ 1.500) e o que manda para uma pessoa.
- Custos de cada ação: só os de `parametros.md` (reenvio = CMV de 24% do valor + frete médio da transportadora; reembolso = valor pago; contato = R$ 9; refazer personalização = custo de reenvio).
- O material do case Atendimento, que ficou fora deste repositório, traz políticas vigentes do grupo. Pode usá-las, sempre como suposição de que valem também para Operações: avaria, vazamento ou item faltante dão reenvio sem custo, mediante foto, em até 7 dias do recebimento; erro de personalização Gocase dá nova produção sem custo, mediante foto, em até 7 dias; arrependimento dá reembolso integral em até 7 dias do recebimento (CDC, art. 49); endereço só pode ser alterado antes da separação.
- **Humano no loop** (sempre em código, nunca no prompt): reembolso acima de um limite que você define e justifica com a distribuição de `valor`; cliente com receita acumulada acima de R$ 1.500; dados incoerentes (ex.: `pagamento_pendente` aguardando transportadora); confiança baixa do agente; todo chamado de processo.

## Modelo de valor em risco (`src/negocio/risco.py`)

Perda esperada de um caso se ele for tratado no dia `d`:

- **Reembolso esperado:** P(cancelamento | dias úteis de atraso em `d`) × valor, pela tabela de `parametros.md`. Vale só para pedido ainda não entregue com risco de atraso.
- **Custo de resolução:** custo da ação da política (reenvio, refação, reembolso).
- **Recompra perdida (estimativa):** P(recompra) × 0,5 × ticket médio do cliente, onde P = 70% se a receita acumulada passa de R$ 1.500 e 28% nos demais casos. Em que condição a exceção conta como "mal resolvida" é uma suposição sua: escreva no SPEC.md.

Cuidado com dupla contagem: um pedido reembolsado não gera também custo de reenvio.

## Priorização (`src/negocio/priorizacao.py`)

Ordene pelo **custo de espera**: quanto a perda esperada cresce se o caso for tratado amanhã em vez de hoje, e não pela perda atual. Um pedido com 12 dias úteis de atraso já está no teto de 40% e quase não piora; um com 2 dias está prestes a saltar de 4% para 10%. Como toda tratativa custa os mesmos 12 minutos, cada dia tem 150 vagas iguais, e escolher o dia de cada caso é um problema de atribuição (casos × vagas), resolvido de forma exata com `scipy.optimize.linear_sum_assignment`. O guloso de um dia (pegar os 150 que mais pioram amanhã) é míope com a tabela em degraus: um caso com 1 dia de atraso não piora amanhã, mas salta depois. Há um teste com esse contraexemplo em `tests/test_negocio.py`. O SPEC.md explica isso em linguagem simples, para quem não é da área de otimização.

Desempate e piso: casos de clientes acima de R$ 1.500 e casos parados há muitos dias não podem ficar presos para sempre. Defina uma regra de envelhecimento e registre como suposição.

## Simulação (`src/negocio/simulacao.py`)

Compare **FIFO** (ordem de `data_abertura_excecao`, o processo atual) com **priorizado**, a partir do estado em 30/09/2026, com 150 tratativas por dia até zerar a fila. Saídas: perda esperada total em cada política, a diferença em R$ (o "quanto a solução recupera") e a curva por dia. Antes de simular, confira se a fila acumulada combina com a capacidade de 150/dia e o ritmo de abertura de exceções. Se não combinar, escreva a explicação adotada como suposição. O resultado vai para `docs/NUMEROS.md` via a skill `dados-operacoes`.

## Recomendações de processo

Para cada padrão de `src/dados/padroes.py`: **dono** (manutenção, supervisão do CD, qualidade/fornecedor, gestão de transportadoras, TI do checkout) · **evidência** (ids de NUMEROS.md) · **ação proposta** · **exceções evitáveis por mês** e **R$ evitado** (estimativa com a conta: exceções acima da taxa de base × custo médio da ação) · **como medir** em 30 dias. O caso do prazo prometido em dias corridos é uma recomendação para TI que elimina exceções na origem; dê destaque a ela.

## README e textos para a banca

Use [README-MODELO.md](README-MODELO.md) como estrutura. Estilo: frases diretas, números com fonte, sem adjetivo de vendedor. Os episódios de "como a IA foi usada e conferida" saem do LOG.md, nunca da imaginação.

## Critérios de qualidade

- Toda regra do SPEC.md cita `parametros.md` ou é uma suposição numerada.
- A política de ações cobre todos os 11 tipos de exceção e diz o que vai para o humano em cada um.
- `risco.py`, `priorizacao.py` e `simulacao.py` não chamam LLM, são determinísticos e têm testes com casos calculados à mão.
- O ganho da solução é uma diferença entre duas políticas na mesma simulação, nunca um número solto.
- Cada recomendação de processo tem dono, número e forma de medir.
- Quem lê o primeiro parágrafo do README sabe quem usa, o que o agente faz e quanto ganha.

## Erros a evitar

- Inventar custo, prazo, política ou volume que não está nos arquivos.
- Priorizar pelo valor do pedido ou pela perda atual em vez do custo de espera.
- Apresentar estimativa como fato: a palavra "estimativa" e a conta acompanham o número em todo lugar.
- Escrever "a IA decide reembolsos": a IA propõe, e o código e a pessoa decidem conforme a política.
- Prometer escopo que a demo não mostra.
