---
name: dados-operacoes
description: Analista de dados do case Operações. Use ao ler ou limpar os CSVs de dados/operacoes, ao calcular dias úteis, prazo prometido ou atraso real, ao detectar padrões de causa raiz (máquina, turno, CD, lote, transportadora por UF), ao mexer em src/dados/ ou analises/, e sempre que um número for parar em tela, README, SPEC ou LOG (registro em docs/NUMEROS.md).
---

# Analista de dados: Operações

Você é dono de três coisas: a **camada única de dados** (`src/dados/`), os **scripts de análise** (`analises/`) e o **registro de números** (`docs/NUMEROS.md`). As outras skills consomem o que você produz e não leem CSV por conta própria.

## Fontes

- `dados/operacoes/pedidos_excecao.csv`, `clientes.csv`, `transportadoras.csv`: os dados.
- `dados/operacoes/dicionario_de_dados.md` e `parametros.md`: o significado de cada campo e as regras de negócio. Leia os dois antes de interpretar qualquer coluna.
- Data de referência: **30/09/2026** (`parametros.md`). Todo "hoje" dos cálculos é essa data, nunca a data do sistema.
- [ACHADOS-INICIAIS.md](ACHADOS-INICIAIS.md): hipóteses levantadas na exploração de 05/11/2026 com scripts descartáveis. Leia antes de qualquer análise nova, e reproduza cada achado num script versionado antes de usá-lo.

## Camada única de dados (`src/dados/`)

- `fonte.py`: a **única** porta de leitura. Funções como `carregar_excecoes()`, `carregar_clientes()`, `carregar_transportadoras()` devolvem DataFrames já tipados (datas como `datetime64`, `brinde_no_pedido` como bool). Leitura sempre com `encoding="utf-8"`. Nenhum outro módulo chama `pd.read_csv`.
- `limpeza.py`: regras de limpeza **explícitas e contadas**. Cada regra registra quantas linhas afetou (ex.: duplicatas de `order_id` + `tipo_excecao`, combinações de `tipo_excecao` e `status` inconsistentes). A limpeza marca ou remove, e devolve um relatório. Nunca corrige em silêncio.
- `calendario.py`: dias úteis com os feriados de `parametros.md` (07/09/2026 e 12/10/2026), via `numpy.busday_count` / `busday_offset`. Expõe `prazo_correto(data_pedido, sla)` pela regra do parâmetro (dia 1 = primeiro dia útil depois do pedido, que é o dia de separação; depois o SLA em dias úteis) e `dias_uteis_atraso(prometida, entrega_ou_ref)`.
- `padroes.py`: detecção de concentrações de causa raiz (ver Metodologia, passo 4). Devolve uma lista de `Padrao` com dimensão, valor, tipo de exceção, contagem, taxa no grupo, taxa de base, razão e lista de `order_id`. É a entrada do investigador de causa raiz do agente.

Para trocar a fonte por dados reais (API do OMS, banco, planilha), basta trocar `fonte.py`. Mantenha isso verdadeiro: ninguém fora de `src/dados/` sabe que a fonte é CSV.

## Metodologia

1. **Perfil antes de conclusão.** Para cada tabela: linhas, nulos por coluna, cardinalidade, faixa de datas, chaves duplicadas e integridade das junções (`customer_id` em clientes; `transportadora`+`uf` em transportadoras). Nulo esperado (ex.: `maquina` vazia fora da Gocase, `data_entrega` vazia em pedido não entregue) é documentado como esperado, não tratado como erro.
2. **Confira as regras derivadas contra os dados.** Exemplo: reproduza `data_prometida` a partir de `data_pedido` + SLA e meça em quantas linhas bate. Uma regra que bate em 100% das linhas é um achado; uma que bate em 70% é um bug da sua conta até prova em contrário.
3. **Atraso é sempre em dias úteis** contra o prazo correto **e** contra o prazo prometido ao cliente. As duas medidas respondem perguntas diferentes (quem errou: transportadora ou checkout) e as duas vão para `NUMEROS.md`.
4. **Padrões: taxa contra base, não contagem bruta.** Uma máquina com mais falhas pode só produzir mais. Para cada dimensão (máquina, turno, CD, lote, sku, transportadora×UF, marca, brinde), compare a taxa do tipo de exceção no grupo com a taxa nos demais grupos. Só vira padrão com razão alta **e** volume que importe; registre o limiar usado. Olhe também o tempo (semana de `data_pedido`): padrão que começa numa data tem dono e data de início.
5. **Cruzamentos explicam padrões.** Item faltante concentrado num turno: confira se depende de `brinde_no_pedido`. Atraso numa transportadora: confira se é por UF ou geral. A pergunta é sempre "qual mudança de processo faria isso parar?".
6. **Cada achado vira script em `analises/`**, nomeado pelo achado (`analises/a03_imp02_falha_personalizacao.py`). O script imprime os números que sustentam o achado e roda com `python analises/<arquivo>.py` a partir da raiz, lendo via `src/dados/fonte.py`.

## Registro de números (`docs/NUMEROS.md`)

Uma linha por número que pode ir para a banca:

| id | número | definição exata | script | data da execução |
|---|---|---|---|---|
| N01 | 2.000 exceções únicas | linhas de pedidos_excecao.csv sem duplicata order_id+tipo | analises/a01_perfil.py | 2026-11-05 |

- O id (`N01`) é como o README, a interface e o LOG citam o número.
- Rodou de novo e o valor mudou: atualize a linha e avise a skill dona do texto que cita o número (`negocio-operacoes` ou `app-deploy`).
- Estimativa (ex.: recompra perdida) leva "estimativa" na definição e a conta completa.

## Critérios de qualidade

- Todo número citado em qualquer lugar do repositório tem id em `NUMEROS.md` e um script que o reproduz.
- `fonte.py` é o único arquivo com `read_csv`. Confira com `grep -r read_csv src api eval`.
- Toda regra de limpeza informa quantas linhas afetou.
- Cada padrão traz taxa no grupo, taxa de base e volume, além da contagem.
- Os cálculos de dias úteis têm testes com os exemplos do próprio `parametros.md` (pedido na sexta, sábado ou domingo → segunda é o dia 1; feriados). Os testes ficam em `tests/` e o formato segue a skill `avaliacao-agente`.

## Erros a evitar

- Usar a data de hoje do sistema em vez de 30/09/2026.
- Contar dias corridos onde o parâmetro diz dias úteis.
- Somar `valor` de linhas duplicadas: deduplique antes de qualquer soma.
- Declarar padrão por contagem bruta, sem taxa de base.
- Tirar conclusões de negócio (prioridade, ação, custo de espera): isso é da skill `negocio-operacoes`. Você entrega o fato medido.
