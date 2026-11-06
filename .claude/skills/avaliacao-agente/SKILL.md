---
name: avaliacao-agente
description: QA e avaliação do projeto. Use ao montar ou revisar o gabarito, ao criar ou rodar eval/eval.py, depois de qualquer mudança de prompt, ferramenta ou regra do agente, ao escrever testes em tests/, ao auditar se os números da tela e do README batem com docs/NUMEROS.md, e ao registrar um erro da IA ou uma mudança de rota no LOG.md.
---

# QA e avaliação

Você é dono de `eval/`, `tests/` e do formato do `LOG.md`. Seu trabalho é transformar "parece funcionar" em número medido, e garantir que cada erro da IA deixe rastro. Isso vale 40% da nota (Modelagem: "você conferiu o que a IA entregou e corrigiu quando ela errou?").

## Gabarito (`eval/gabarito.jsonl`)

Uma linha por caso: `order_id`, `tipo_excecao`, `acao_esperada`, `acoes_aceitaveis` (lista, para casos em que a política admite mais de uma), `deve_ir_para_humano`, `motivo_humano_esperado`, `padrao_esperado` (id ou nulo), `racional` (por que essa é a resposta, citando SPEC.md ou parametros.md), `anotado_por` (`levi` ou `claude_revisado_por_levi`).

Composição (de 25 a 35 casos, escolhidos por script com semente fixa e sorteio estratificado):
- pelo menos 2 casos de cada um dos 11 tipos de exceção;
- casos de cada padrão de `src/dados/padroes.py` e casos fora de padrão;
- casos difíceis: atraso dentro do SLA contratado, cliente acima de R$ 1.500, status incoerente, duplicata, pedido já entregue com exceção de atraso;
- casos em que a resposta certa é mandar para o humano.

Processo de anotação: você propõe o rótulo com o racional, e o Levi confirma ou corrige. O gabarito é anotado **antes** de olhar a saída do modelo para aquele caso. Corrigir o gabarito depois de ver o modelo errar exige uma linha no LOG.md explicando por que o gabarito estava errado, e não o modelo.

## Eval (`eval/eval.py`)

- Roda `processar()` (a mesma função da interface) em todos os casos do gabarito. Por padrão chama o modelo ao vivo; `--demo` usa o cache.
- Imprime o acerto **por etapa**: ação (exata e aceitável), decisão de humano (precisão e recall de "deve ir para humano"), padrão, JSON válido na primeira tentativa, além do tempo e dos tokens por caso.
- Imprime a lista de erros com `order_id`, esperado × obtido e a justificativa do modelo, para leitura rápida.
- Salva `eval/resultados/<AAAA-MM-DD_HHMM>_v<versao_prompt>.json` com o resultado completo. O README cita o último resultado.
- A métrica que mais importa é o recall de "deve ir para humano": caso de risco tratado sozinho é o erro caro. Mostre-a em destaque.
- Rode duas vezes antes de afirmar uma melhora pequena: com `temperature=0` ainda pode haver variação. Diferença de 1 caso em 30 não é melhora.

## Testes (`tests/`, pytest)

Cobrem o que é determinístico e não pode errar:
- `src/dados/calendario.py`: os exemplos do próprio `parametros.md` (pedido na sexta, sábado ou domingo → segunda é o dia 1), feriados de 07/09/2026 e 12/10/2026, e as faixas da tabela de cancelamento (2, 3, 5, 6, 10 e 11 dias úteis).
- `src/negocio/risco.py` e `priorizacao.py`: casos calculados à mão, com a conta no docstring do teste.
- `src/agente/regras.py`: cada regra de humano no loop tem um teste que a dispara e outro que não dispara.
- `src/agente/esquemas.py`: JSON inválido é rejeitado; `precisa_humano` verdadeiro sem motivo é rejeitado.
- Um teste de fumaça: `processar(..., modo="demo")` devolve `Resultado` válido para todos os casos em cache.

## Auditoria de números

Antes de qualquer entrega ou deploy: liste os números do README, do SPEC.md e dos textos de `web/`, e confira cada um com o id em `docs/NUMEROS.md`. Número sem id ou com valor divergente é um defeito: devolva para a skill dona do texto.

## LOG.md

Formato de cada entrada:

```
## 2026-11-06 14:20: [erro da IA | mudança de rota | decisão | feedback]
- O que aconteceu: ...
- Como percebemos: (eval, teste, revisão manual, Levi)
- O que mudou: (arquivo, versão do prompt)
- Antes → depois: (ex.: ação 21/30 → 26/30; recall humano 5/8 → 8/8)
```

Entram: erro do modelo do produto, erro do Claude Code que o Levi ou um teste pegou, abordagem abandonada e o motivo, ajuste no gabarito. Use a data e a hora reais (`date`). Escreva no momento em que acontece, porque é daqui que sai a seção do README sobre como a IA foi conferida.

## Critérios de qualidade

- `python eval/eval.py` roda a partir da raiz e termina imprimindo um resumo de uma tela.
- Cada mudança de prompt, ferramenta ou regra tem um resultado de eval antes e depois no LOG.md.
- `pytest` passa antes de qualquer commit que mexa em `src/`.
- Todo número público está auditado contra `docs/NUMEROS.md`.

## Erros a evitar

- Medir só o acerto total: um acerto alto pode esconder recall baixo de "deve ir para humano".
- Gabarito com casos fáceis demais, ou anotado olhando a saída do modelo.
- Exemplos do prompt sobrepostos ao gabarito: confira os `order_id`.
- Relatar "melhorou" sem rodar o eval, ou com uma rodada só numa diferença de 1 caso.
- Apagar ou suavizar uma entrada antiga do LOG.md: erro registrado é evidência a favor.
