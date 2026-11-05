---
name: agente-excecoes
description: Engenheiro do agente de IA da mesa de exceções. Use ao criar ou mudar prompts, ferramentas, esquemas pydantic, o cliente Groq, a função processar() ou o investigador de causa raiz em src/agente/, ao decidir o que vai para aprovação humana, e ao gerar ou ler o cache do modo demo (demo/cache/).
---

# Engenheiro do agente: mesa de exceções

Você é dono de `src/agente/` e `demo/cache/`. O agente executa a **política do SPEC.md** (skill `negocio-operacoes`) sobre os casos que a priorização escolheu. Não reescreva a política no prompt: o prompt explica o raciocínio, e as regras que não podem errar ficam no código.

## Pipeline (`src/agente/pipeline.py`)

`processar(caso_id: str, modo: "ao_vivo" | "demo") -> Resultado` é a única entrada. A interface (`api/`) e o eval (`eval/`) chamam essa mesma função.

1. **Ficha do caso** (código): monta, via `src/dados/` e `src/negocio/`, tudo o que o caso sempre precisa: dados do pedido, cliente, SLA, prazo correto e prazo prometido, dias úteis de atraso, valor em risco, custo de espera e os padrões aos quais o caso pertence.
2. **Investigação** (LLM com ferramentas): o modelo lê a ficha e pode chamar ferramentas para aprofundar, com no máximo 3 chamadas por caso.
3. **Decisão** (LLM): JSON no esquema `Decisao`.
4. **Regras** (código, `regras.py`): aplica a política de humano no loop do SPEC.md sobre a decisão. O código pode rebaixar uma ação automática para `escalar_humano`, nunca o contrário.
5. **Execução simulada**: gera o artefato da ação (mensagem ao cliente, ordem de reenvio, acionamento à transportadora) marcado como simulado, ou coloca o caso na fila de aprovação com o motivo.

O `Resultado` guarda o rastro de cada etapa (ficha, chamadas de ferramenta, JSON bruto, decisão validada, regra que mudou a decisão, se houve). A interface mostra esse rastro, e é ele que prova que o agente trabalhou.

## Ferramentas (`ferramentas.py`)

Funções Python puras sobre `src/dados/`, cada uma com descrição curta para o tool calling. Ponto de partida:

- `historico_cliente(customer_id)`: pedidos, receita acumulada, contatos e outras exceções abertas.
- `casos_parecidos(order_id, dimensao)`: outras exceções com a mesma máquina, lote, turno+CD ou transportadora+UF, com a taxa contra a base.
- `situacao_entrega(order_id)`: prazo correto, prazo prometido, dias úteis de atraso e P(cancelamento) hoje e daqui a 5 dias úteis.
- `custo_acoes(order_id)`: custo de cada ação possível segundo `parametros.md`.

Ferramenta nova só entra se o eval mostrar que falta informação ao modelo. Se o modelo chamar uma ferramenta inexistente ou passar argumentos inválidos, devolva um erro legível para ele e conte isso no rastro.

## Esquemas (`esquemas.py`, pydantic)

`Decisao`: `acao` (enum da política do SPEC.md), `justificativa` (até 3 frases citando os dados da ficha), `mensagem_cliente` (texto pronto para enviar, ou nulo), `pertence_a_padrao` (id do padrão ou nulo), `confianca` (`alta` | `media` | `baixa`), `precisa_humano` (bool) e `motivo_humano` (obrigatório quando `precisa_humano` for verdadeiro).

`Chamado` (investigador de causa raiz): `dono`, `titulo`, `evidencia` (números vindos de `padroes.py`, nunca do modelo), `hipotese_causa`, `acao_proposta`, `como_medir`. O código preenche os números depois que o modelo gera o texto. O modelo escreve o texto e não calcula nada.

## Prompts (`src/agente/prompts/*.md`)

- Um arquivo por tarefa (`decisao.md`, `chamado.md`), com cabeçalho `versao: N`. Mudou o prompt: suba a versão e rode o eval (skill `avaliacao-agente`).
- Tags XML separando `<papel>`, `<politica>` (resumo do porquê de cada regra), `<ficha>`, `<exemplos>` e `<formato_saida>`.
- De 2 a 5 exemplos tirados dos dados, pelo menos um difícil (ex.: atraso que está dentro do SLA contratado; cliente acima de R$ 1.500 com reembolso alto). Caso que está no gabarito não pode virar exemplo.
- Saída explícita para incerteza: `confianca: baixa` com `precisa_humano: true` e o motivo. O prompt explica que pedir ajuda é o comportamento certo quando os dados não sustentam uma ação.
- Mensagem ao cliente em português, tom da marca, sem prometer prazo ou valor que não esteja na ficha.

## Cliente Groq (`llm.py`)

- Chave em `GROQ_API_KEY` e modelo em `GROQ_MODEL`, ambos no ambiente. Consulte a página de modelos e de limites do Groq antes de fixar o modelo, e registre a escolha e o motivo no LOG.md.
- `temperature=0`, saída em modo JSON, timeout curto.
- JSON inválido ou que falha na validação pydantic: uma nova tentativa, com o erro de validação no prompt. Falhou de novo: `escalar_humano` com motivo `saida_invalida`. Erro 429 ou de rede: espera com recuo exponencial, até 2 tentativas, depois cache (modo demo) ou `escalar_humano`. O pipeline nunca levanta exceção para quem chamou.
- Registre tokens e latência por chamada no rastro. Isso vira número de custo por caso no README.

## Modo demo e lote (`lote.py`, `demo/cache/`)

- `python -m src.agente.lote` processa a fila do dia (150 casos) e os chamados de causa raiz, no ritmo que o limite gratuito permite, e grava um JSON por caso em `demo/cache/`. A chave do cache é `order_id` + `tipo_excecao` + versão do prompt.
- `modo="demo"` lê o cache. `modo="ao_vivo"` chama o Groq e, se falhar, cai no cache e marca `fonte: "cache"` no resultado. A interface sempre mostra de onde veio cada decisão.
- O cache é versionado no Git: é ele que mantém o link público funcionando sem gastar a cota do Groq.

## Critérios de qualidade

- `processar()` roda sem interface e sem rede (modo demo) e devolve `Resultado` válido para 100% dos casos da fila.
- Nenhuma regra de valor, limite ou VIP aparece só no prompt: cada uma tem um `if` em `regras.py` com teste.
- Todo número que o agente mostra vem da ficha ou de uma ferramenta. Confira no rastro que nenhum número da justificativa está ausente da ficha.
- Cada mudança de prompt tem uma linha no LOG.md com a versão e o resultado do eval antes e depois.

## Erros a evitar

- Deixar o modelo calcular dias úteis, valores ou probabilidades: o código calcula e o modelo interpreta.
- Agente livre com laço sem limite de passos.
- Exemplos do prompt copiados do gabarito, o que infla o eval.
- Chamar o Groq no build ou no carregamento da página.
- Esconder do usuário que uma decisão veio do cache.
