# CLAUDE.md: Mesa de Exceções (Desafio AI-First Gogroup, case Operações)

Projeto do Levi (estudante de CC na UFC) para a etapa 3 do processo seletivo de estágio em IA do Gogroup. Enunciado em `Desafio_AI-First_Gogroup.pdf`; dados em `dados/operacoes/`. Os outros dois cases do desafio foram tirados do projeto de propósito; não os procure.

## Decisões já tomadas

- **Case:** Operações. **Recorte:** mesa de exceções do dia. O código prioriza a fila dentro da capacidade de 150 tratativas/dia; um agente de IA investiga cada caso da fila, propõe a ação e redige a mensagem; um investigador de causa raiz agrupa exceções com a mesma origem e redige o chamado para o dono do processo. Uma pessoa aprova o que é caro, arriscado ou incerto.
- **Prazo:** 10/11/2026. Hoje é o que `date` disser; converta datas relativas em absolutas em todo registro.
- **Dados no repositório:** o Levi decidiu versionar os CSVs sintéticos. Não reabra essa discussão.
- **Modelo:** Groq gratuito (Llama), chave em `GROQ_API_KEY` no `.env` (no `.gitignore`). Nenhuma chave no código nem no front.
- **Entrega:** link público sem login (Vercel) + repositório público no GitHub.
- **Stack:** núcleo em Python 3.12 (pandas, pydantic, SDK `groq`), API FastAPI como função Python da Vercel em `api/`, front React + TypeScript (Vite) em `web/`. Trocar de stack exige ok do Levi.

## Como a banca avalia (pese toda decisão contra isto)

| Critério | Peso | Na prática, neste projeto |
|---|---|---|
| Modelagem | 40% | Fluxo de ponta a ponta funcionando; agente com autonomia sobre o lote inteiro; eval com gabarito; erros da IA registrados e corrigidos |
| Adaptabilidade | 20% | Uso dos dados sintéticos com números; camada única de dados; seção "Com dados reais"; mudanças de rota registradas |
| Conceito | 20% | Persona, dor e ganho entendidos em 10 segundos, na tela e no README |
| Aderência cultural | 20% | Dono do problema: recomendações de processo com número, LOG.md honesto, próximos passos |

Não há pitch ao vivo: README e interface fazem esse papel. Desempate por Modelagem, depois Conceito.

## Skills do projeto (`.claude/skills/`)

Cada skill é dona de uma parte do repositório. Antes de mexer numa parte, carregue a skill dona dela.

| Skill | Dona de | Acione quando |
|---|---|---|
| `dados-operacoes` | `src/dados/`, `analises/`, `docs/NUMEROS.md` | ler/limpar CSVs, calcular dias úteis e atraso, detectar padrões, produzir qualquer número |
| `negocio-operacoes` | `SPEC.md`, `src/negocio/`, `README.md` (conteúdo) | persona, valor em risco, priorização, simulação, recomendações de processo, textos para a banca |
| `agente-excecoes` | `src/agente/`, `demo/cache/` | prompts, ferramentas, esquema JSON, chamadas ao Groq, `processar()`, humano no loop, modo demo |
| `avaliacao-agente` | `eval/`, `tests/`, formato do `LOG.md` | gabarito, `eval.py`, testes, auditoria de números, registro de erros da IA |
| `app-deploy` | `api/`, `web/`, `vercel.json`, `requirements.txt` | interface, endpoints, deploy na Vercel, variáveis de ambiente |

Fluxo entre elas: `dados` produz fatos e números → `negocio` transforma em regra de prioridade e política (SPEC.md) → `agente` executa a política com o LLM → `avaliacao` mede contra o gabarito e registra erros → `app` mostra tudo. Achado novo de uma skill que afeta outra vai para o arquivo compartilhado certo (abaixo), nunca só para a conversa.

## Avaliador cego

`.claude/agents/recrutador-gogroup.md` simula o recrutador do Gogroup. Ele avalia só o link público, o repositório e o enunciado, sem o contexto das sessões, e decide se contrataria. Rode quando o Levi pedir ("roda o recrutador") e transforme o relatório em melhorias priorizadas. Não passe a ele dicas sobre o projeto: o valor dele está em ser cego.

## Arquivos compartilhados (fonte única de verdade)

- `SPEC.md`: persona, dor, fluxos atual e novo, métricas, definição do pronto, **política de ações** e **suposições**. Regra de negócio que não está aqui nem em `dados/operacoes/parametros.md` não existe.
- `docs/NUMEROS.md`: todo número que aparece em tela, README ou LOG, com valor, script que o gera e data da última execução. Número fora dessa tabela não vai para a banca.
- `LOG.md`: erros da IA (sua ou do modelo do produto) e correções, mudanças de rota e decisões, com data e hora, e números antes e depois. Escreva sem esperar pedido.

## Arquitetura

```
dados/operacoes/*.csv  →  src/dados/fonte.py (única porta de leitura)
                          src/dados/{calendario,limpeza,padroes}.py
                       →  src/negocio/{risco,priorizacao,simulacao}.py   (determinístico, sem LLM)
                       →  src/agente/pipeline.py: processar(caso) → Decisao   (LLM + ferramentas + regras)
                       →  eval/eval.py e api/index.py chamam a MESMA processar()
                       →  web/ consome a API; demo/cache/ guarda saídas para o modo demo
```

Etapas do agente: **ficha do caso** (código) → **investigação** (LLM com ferramentas) → **decisão** em JSON validado → **regras de negócio em código** (limites, VIP, confiança) → **execução simulada** (mensagem, reenvio, acionamento) ou **fila de aprovação humana** com o motivo.

## Princípios de desenvolvimento

- **Ponta a ponta primeiro.** Um fluxo completo e simples antes de melhorar qualquer etapa.
- **Regras que não podem errar ficam em `if`**, não no prompt: valores, prazos, limites de aprovação.
- **Saída do modelo sempre em JSON validado com pydantic.** Inválido: uma nova tentativa; inválido de novo: humano, com motivo. O app nunca quebra na frente de quem abre o link.
- **Nenhum número inventado.** Todo número sai de script versionado e entra em `docs/NUMEROS.md`, ou aparece marcado como estimativa com a conta. O que for simulado, a tela diz que é simulado.
- **Toda mudança de prompt é seguida de uma rodada do eval**, com o resultado no LOG.md.
- **Verifique antes de dizer que funciona:** rode o comando (teste, eval, build, script) e mostre o comando e a saída.
- **Commits pequenos** com mensagem que conta o avanço ("eval: decisão acerta 26/30"). Só faça commit ou push quando o Levi pedir.
- **Dados de referência:** consulte `dados/operacoes/dicionario_de_dados.md` e `parametros.md` antes de supor qualquer regra. Dúvida de negócio que os dados não respondem: pergunte ao Levi ou registre como suposição no SPEC.md.

## Como trabalhar com o Levi

- Português, respostas curtas. Antes de uma mudança grande, mostre o plano em poucas linhas e espere o ok; mudança pequena, faça e mostre.
- Ao fechar uma etapa: 2 ou 3 linhas com o que mudou, como foi verificado e o próximo passo.
- Explique decisões técnicas de forma que ele consiga repetir numa entrevista; ele precisa entender tudo o que está no repositório.
- Todo texto que a banca lê (README, textos da interface, SPEC.md) passa pela skill `humanizar` antes de entrar no repositório. Estilo: frases diretas, fatos e números do projeto, episódios reais do LOG.md.
- Se ele pedir algo que tira pontos (número sem fonte, troca de stack tarde, funcionalidade fora da demo perto do prazo), avise em uma frase e deixe ele decidir.
