# Mesa de exceções

A Mesa de exceções separa, com um algoritmo de otimização, os 150 pedidos com problema que valem mais ser tratados hoje, e um agente de IA propõe o que fazer em cada um, para que a analista de exceções do Gogroup pare de trabalhar a fila por ordem de chegada e perca menos dinheiro com cancelamentos. No estoque acumulado até 30/09/2026, o plano do agente reduz a perda esperada em R$ 17.448 [N72] (15% [N73], estimativa). Esse ganho é de uma vez, sobre a fila que já existe, e não mensal. Os casos caros, sensíveis ou incertos vão para uma pessoa.

- App: https://mesa-de-excecoes.vercel.app (sem login)
- Feito para o Desafio AI-First do Gogroup, case Operações, com os dados sintéticos do desafio. A persona (Juliana) é fictícia, e as ações são simuladas: nada é enviado a clientes.
- O enunciado e os CSVs do desafio não estão neste repositório, porque o enunciado pede para não compartilhá-los. Para rodar a análise, coloque os arquivos do case Operações em `dados/operacoes/`. O repositório traz só o que a interface precisa: a fila do dia, as decisões e os números agregados.

**Como usar em 30 segundos:** abra o link, leia a régua do topo (ordem de chegada contra o plano do agente), clique num caso laranja da fila ("aguarda a Juliana") para ver por que ele foi para uma pessoa, e num caso verde para ver a decisão e a mensagem que o agente escreveu. O botão "Rodar o agente agora" chama o modelo ao vivo.

## O problema

Há 2.000 exceções abertas [N01] (atraso, extravio, avaria, falha de personalização, pagamento pendente, ruptura, endereço divergente e outras). O time trata 150 por dia, de 12 minutos cada (`parametros.md`), o que dá 13,3 dias de fila [N05]. A fila anda por ordem de chegada.

A ordem importa porque o risco de cancelamento cresce em degraus com os dias úteis de atraso (4%, 10%, 22%, 40%). Um pedido que vai subir de faixa amanhã espera atrás de outro que já está no teto e não piora mais. E ninguém olha a fila como um todo: 46% das exceções [N32] vêm de 6 causas de processo [N30] que se repetem, e 30% dos "atrasos" [N23] não são atraso da transportadora. O checkout calcula a data prometida em dias corridos [N20], mas o SLA contratado é em dias úteis.

## O que o agente faz

```
dados (CSV)  ->  ficha do caso           código: prazos em dias úteis, risco, padrão
             ->  plano do dia            código: atribuição ótima casos x dias (150/dia)
             ->  decisão                 LLM: lê a ficha, propõe ação + mensagem (JSON validado)
             ->  regras H1-H7            código: caro, sensível ou incerto vai para a Juliana, com o motivo
             ->  execução simulada       mensagem; reenvio que depende de foto espera a foto
padrões      ->  chamado de causa raiz   código mede, LLM redige, a Juliana aprova
```

1. Prioriza. O custo de cada caso depende do dia em que ele é tratado. Escolher o dia de cada um minimizando a perda total é um problema de atribuição (casos × vagas de 150 por dia), resolvido de forma exata pelo algoritmo húngaro (`src/negocio/priorizacao.py`). A primeira versão usava um guloso que olha só o dia seguinte, e ele não serve: um caso com 1 dia de atraso não piora amanhã, mas salta depois de amanhã (teste `test_otimo_olha_alem_de_amanha`).
2. Decide. Para cada caso da fila, o modelo (`openai/gpt-oss-120b` no Groq) recebe a ficha montada pelo código e devolve ação, justificativa e mensagem ao cliente num JSON validado com pydantic. Os números vêm todos da ficha: o modelo interpreta e não calcula. O agente tem duas ferramentas de consulta (`historico_cliente` e `casos_parecidos`), mas em 182 decisões não chamou nenhuma: a ficha já traz o que ele precisa, inclusive o padrão de causa raiz. Deixei as ferramentas no código porque com dados reais a ficha não vai trazer tudo; hoje, na prática, a decisão é uma chamada ao modelo por caso.
3. Pede ajuda. As regras de revisão humana ficam no código, não no prompt (`src/agente/regras.py`): registro incoerente, reembolso acima de R$ 228 [N13], reenvio acima de R$ 73 [N68], reembolso para cliente acima de R$ 1.500, atraso sem entrega acima de 10 dias úteis, reclamação fora do prazo da política, confiança baixa do agente e mensagem de reenvio que não pede a foto exigida. O código pode mandar um caso para a Juliana, mas nunca tira um caso dela.
4. Abre chamados. O código detecta onde as exceções se concentram, comparando com a taxa dos demais grupos, e o agente escreve um chamado para o dono do processo.

Dois casos reais da fila:
- **Resolvido sozinho (GC7003305, prioridade 18):** um atraso que passou da data prometida, mas está dentro do SLA contratado. Uma automação por tipo cobraria a transportadora. O agente percebe que quem errou foi a data prometida, e escreve ao cliente com o prazo correto.
- **Foi para a Juliana (GB7005077, prioridade 23):** um pagamento pendente com status "aguardando transportadora". O registro está incoerente (regra H1), então o agente não age em cima dele.

## Resultado

**Priorização** (estoque de 30/09/2026, 150 tratativas por dia útil, estimativa):

| Política | Perda esperada |
|---|---|
| Ordem de chegada (hoje) | R$ 112.698 [N70] |
| Maior perda atual primeiro | R$ 108.322 [N76] |
| Maior valor de pedido primeiro | R$ 101.908 [N75] |
| Plano do agente | R$ 95.249 [N71] |

O plano captura 93% [N74] da perda que dá para evitar mudando só a ordem. A perda soma reembolso esperado (exceto em pagamento pendente, em que o dinheiro não entrou), recompra perdida e custo de reenvio; o modelo e as suposições estão no [SPEC.md](SPEC.md).

**Agente** (`python -m eval.eval`, prompt v2, `openai/gpt-oss-120b`; resultado ao vivo em `eval/resultados/2026-11-05_1907_v2.json` e, com as regras atuais reaplicadas às mesmas decisões, em `eval/resultados/2026-11-06_0955_v2_demo.json`):

| Medida | Resultado | Quem faz |
|---|---|---|
| Casos de risco que foram para a Juliana | 5 de 5 | código (regras H1, H2b e H4) |
| Ação certa pela política | 33 de 33 | modelo, conferido pelas regras |
| Tabela de política escrita em código (sem modelo) | 33 de 33 | código |
| Automação ingênua (ação fixa por tipo) | 26 de 33 | código |
| Mensagens sem problema nas checagens automáticas | 33 de 33 | modelo |
| JSON válido na primeira tentativa | 33 de 33 | modelo |
| Casos adversariais (`python -m eval.adversariais`) | 4 de 4 | modelo (3) e código (1) |

O gabarito tem 33 casos sorteados com semente fixa, cobrindo os 11 tipos de exceção e os casos difíceis. Os rótulos foram propostos pela própria tabela de política (`eval/montar_gabarito.py`) e depois revisados caso a caso contra o texto do SPEC, primeiro pelo Claude Code e depois por mim. A revisão concordou com os 33 e apontou uma lacuna da política: rastreio parado há mais de 30 dias úteis provavelmente é extravio, mas a regra manda só cobrar a transportadora. Por isso a tabela em código acerta 33 de 33 por construção, e acertar a ação não prova, sozinho, que o modelo é necessário: para os casos que a política já prevê, um `if` faz o mesmo trabalho.

O que o modelo faz e o código não faz:
- escreve a mensagem para o cliente de cada caso, com a data e o pedido certos (33 de 33 sem problema nas checagens);
- lida com o que a tabela não prevê: num tipo de exceção que não existe na política, a tabela quebra e o modelo pede revisão (caso adversarial A3);
- ignora uma instrução injetada no nome do produto (caso A1);
- escreve a justificativa e os chamados de causa raiz em linguagem que o dono do processo entende.

Na fila do dia inteira, com 150 [N100] casos decididos, 144 [N101] decisões batem com a tabela de política, 147 [N103] das 149 mensagens passam nas checagens automáticas e 8 [N102] casos foram para a Juliana. Essa conferência é automática, contra a mesma tabela (`analises/a06_fila_do_dia.py`). Uma das 6 divergências é o GB7000254: a regra H7 mandou o caso para a Juliana porque o modelo tinha dispensado a foto do cliente.

## O que está causando as exceções

Estimativas por mês, contando só as exceções acima da taxa de base do grupo:

| Causa | Dono | Proposta | Exceções evitáveis por mês |
|---|---|---|---|
| Data prometida em dias corridos [N20] | TI do checkout | calcular em dias úteis, como manda o SLA | 76 [N95] |
| Rota Express no Nordeste: entrega 3,0 [N54] dias úteis além do SLA, contra 0,8 [N55] nas demais | Gestão de transportadoras | cobrar o SLA, avaliar multa, testar outra transportadora | 161 [N80] |
| CD2, turno da noite: item faltante, 75% [N52] com brinde (36% [N53] na base) | Supervisão do CD2 | conferência do brinde na separação noturna | 98 [N82] |
| Carga Norte: avaria no transporte | Gestão de transportadoras | revisar embalagem e manuseio | 41 [N84] |
| Lote L2607-B do APC-1067: vazamento | Qualidade / fornecedor | bloquear o lote | 38 [N86] |
| Impressora IMP-02: falha de personalização desde 24/08/2026 [N50] | Manutenção | manutenção e redistribuir a produção | 31 [N88] |
| Kokeshi: ruptura depois da venda | Compras | revisar estoque de segurança | 26 [N90] |

Somando sem contar duas vezes, são cerca de 430 [N97] exceções por mês, ou 86 h [N98] de trabalho do time.

## Como a IA foi usada e conferida

Construí o projeto com o Claude Code. Cada etapa passa por teste, eval ou cruzamento de dados, e o [LOG.md](LOG.md) registra cada erro encontrado, com o antes e o depois. Alguns exemplos:

- O primeiro detector de padrões apontou um falso padrão (um SKU com falhas de personalização). O cruzamento por máquina mostrou que 11 das 23 falhas vinham da IMP-02. O detector passou a exigir que o padrão se sustente só com os casos que nenhum outro já explica.
- A primeira especificação da priorização era um guloso de um dia. Na implementação ficou claro que ele é míope com a tabela em degraus, e ele foi trocado pela atribuição exata.
- Os exemplos do prompt saíram com 5 fatos escritos de memória pela IA (datas, receita de cliente, marcas). Cada exemplo foi conferido contra a ficha real antes da primeira chamada ao modelo.
- O primeiro eval deu 100%, o que levantou suspeita. A checagem automática de mensagens achou um erro do modelo (pediu "foto ou endereço" num atraso) e virou o prompt v2. Um caso adversarial mostrou que o modelo não percebia uma ficha contraditória, e essa checagem foi para o código.
- No primeiro teste do link publicado, o erro do Groq voltava cru ao navegador, com o id da organização da conta. Agora a mensagem é genérica e o detalhe fica no log do servidor.
- Criei um avaliador cego (`.claude/agents/recrutador-gogroup.md`): um agente que avalia só o link, o repositório e o enunciado, como a banca faria. Ele achou 3 problemas que meus testes não pegaram. As ferramentas do agente nunca eram chamadas e o README dizia o contrário. O 20b disse a um cliente que ele não precisava mandar foto, e o checador de mensagens deixou passar porque só procurava a palavra "foto". E havia 52 reenvios automáticos sem limite de valor. Viraram as regras H2b e H7 (com testes), a correção do checador e esta seção de resultados, que agora separa o que é do código e o que é do modelo.

## Como rodar

```bash
# antes: copie os arquivos do case Operações do desafio para dados/operacoes/
pip install -r requirements-dev.txt
cp .env.example .env              # coloque GROQ_API_KEY
python -m pytest                  # testes de calendário, risco, priorização, regras e esquemas
python -m analises.gerar_numeros  # recalcula docs/NUMEROS.md
python -m eval.eval               # eval ao vivo (ou --demo, que usa o cache)
python -m eval.adversariais
python -m src.agente.lote         # decide a fila do dia e grava demo/cache/
python -m src.agente.investigador # redige os chamados de causa raiz
python -m src.exportar            # gera os JSON da interface
uvicorn api.index:app --port 8000 # API local
cd web && npm install && npm run dev
```

Cada número entre colchetes neste README, como [N01], está em [docs/NUMEROS.md](docs/NUMEROS.md) com a definição e o script que o gera. O `python -m eval.auditar_numeros` confere se os valores do README, do SPEC e da interface batem com esse registro.

## Com dados reais

- **Fonte:** só `src/dados/fonte.py` lê dados. Trocar os CSVs pelo OMS (pedidos e exceções), pelo CRM (clientes) e pelos contratos com as transportadoras exige mexer só nesse arquivo, mantendo as colunas.
- **Taxas de padrão:** com o total de pedidos por máquina, turno e transportadora, as taxas passam a ser sobre todos os pedidos, e não só sobre as exceções (suposição S11).
- **Volume:** a fila real tem a mesma ordem de grandeza (algumas centenas por dia). O plano roda em segundos. No plano gratuito do Groq, o modelo aceita 8.000 tokens por minuto e 200.000 por dia, o que dá cerca de 66 decisões por dia (cada uma gasta uns 3.000 tokens). Foi por isso que a fila de demonstração levou dois dias para ser processada. Em produção, um plano pago resolve 150 casos em poucos minutos.
- **Validação:** a suposição mais importante é a S2 (tratar o caso trava o atraso). Eu mediria isso com um piloto A/B: metade da fila em ordem de chegada, metade pelo plano, comparando cancelamentos em 30 dias.
- **LGPD:** a ficha que vai ao modelo não precisa de nome, CPF nem endereço completo do cliente, só cidade e UF. Com dados reais, manter assim e registrar a base legal do tratamento.

## Limitações e próximos passos

- Ações simuladas: falta integrar com o envio de mensagens e com a abertura de reenvio.
- O ganho em R$ é estimativa de modelo (tabela de cancelamento e recompra do `parametros.md`), não medição. E ele é de uma vez, sobre a fila acumulada. Como abrem de 33 [N06] a 42 [N07] exceções por dia e o time trata 150, depois que o estoque zera a ordem pesa menos. O ganho recorrente viria do replanejamento diário e das mudanças de processo (430 [N97] exceções evitáveis por mês), e não foi estimado em R$.
- A regra H7 reconhece a dispensa da foto por expressão regular, e paráfrases como "não é preciso enviar foto" passam. O conserto certo é o modelo devolver um campo `pede_foto` no JSON, conferido contra a mensagem.
- Comparei o plano só com políticas ingênuas. Uma ordenação simples, "mais novo primeiro", já chega perto do plano ótimo, porque os casos mais antigos já estão no teto de risco; o algoritmo exato acrescenta pouco sobre uma boa regra de ordenação.
- O plano é escolhido e avaliado pela mesma função de perda. O ganho depende da suposição S2 (tratar o caso trava o atraso), que só um piloto mede.
- O gabarito foi revisado por mim, e não por alguém da operação, e precisa de casos difíceis vindos de exceções reais. A revisão também achou uma lacuna na política: rastreio parado há mais de 30 dias úteis deveria virar extravio (reenvio) ou ir para a analista.
- Os dois modelos às vezes confundem "7 dias do recebimento" com dias desde a abertura do caso. Na maioria das vezes isso manda para a Juliana um reenvio que poderia ser automático; no GB7000254 levou o modelo a dispensar a foto, e quem segurou foi a regra H7. A correção é tirar essa regra do prompt, porque o código já a verifica (regra H5), e rodar o eval de novo.
- Fila com dois modelos: o limite diário do plano gratuito acabou no meio do lote, e parte da fila foi decidida pelo `openai/gpt-oss-20b`. Antes de usá-lo, ele passou pelo mesmo eval (`eval/resultados/2026-11-05_2016_v2_gpt-oss-20b.json`): mandou para a pessoa os 4 de 4 casos de risco e acertou a ação em 31 de 33, e os 2 erros foram envios desnecessários à pessoa. A tela mostra qual modelo decidiu cada caso.
- Próximo passo: replanejar a cada dia com as exceções novas e medir o acerto do agente contra a decisão final da analista.
