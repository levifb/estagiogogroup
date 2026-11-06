# LOG

Erros da IA (do Claude Code e do modelo do produto) e as correções, mudanças de rota, decisões e feedbacks, em ordem. Formato definido na skill `avaliacao-agente`.

## 2026-11-05: decisão
- O que aconteceu: comparei os três cases com perfis rápidos dos dados e escolhi Operações.
- Por quê: os dados de Operações têm causas de processo mensuráveis (máquina, turno, lote, transportadora por UF, cálculo do prazo prometido), e os parâmetros dão o custo de cada decisão. Isso permite medir em R$ o efeito da priorização e do agente.
- Recorte: mesa de exceções do dia. O código prioriza 150 casos por dia, o agente decide a ação de cada um e o investigador de causa raiz abre chamados para o dono do processo.

## 2026-11-05: decisão
- Os CSVs sintéticos vão para o repositório público (decisão do Levi). Os dados dos outros dois cases ficaram fora do projeto.

## 2026-11-05 18:37: erro da IA (detector de padrões)
- O que aconteceu: a primeira versão de `src/dados/padroes.py` (escrita pelo Claude Code) apontou grupos amplos demais ("CD2", "marca Ápice") em vez do recorte que tem dono ("CD2 no turno da noite", "lote L2607-B do APC-1067"). Também comparou a taxa da IMP-02 com pedidos que nem passam por máquina, o que deu base de 3% em vez de 11%.
- Como percebemos: comparação com os achados da exploração inicial, que já apontavam o turno e o lote.
- O que mudou: a base passou a ser calculada só onde a dimensão existe, e o detector troca o grupo amplo por um recorte que explique pelo menos 80% do excesso.
- Antes → depois: 8 padrões, com 2 amplos demais → padrões no recorte certo (N40 a N45).

## 2026-11-05 18:37: erro da IA (padrão falso por confusão de causa)
- O que aconteceu: o detector aceitou "SKU GOC-2001 com falha de personalização" como padrão próprio.
- Como percebemos: cruzamento por máquina. 11 das 23 falhas vinham da IMP-02, e fora dela o SKU fica perto da base (12 de 82, 15% contra 11%).
- O que mudou: um padrão só é aceito se continuar acima da base contando apenas os casos que nenhum padrão já aceito explica.
- Antes → depois: 7 padrões → 6 (N30); exceções explicadas 926 → 914 (N31).

## 2026-11-05 18:37: erro da IA (contagem de atraso)
- O que aconteceu: o script versionado deu 157 atrasos "dentro do SLA", e a exploração inicial tinha dado 147.
- Como percebemos: conferência do número novo contra o anotado em ACHADOS-INICIAIS.md.
- Causa: entrega no sábado ou domingo depois de um prazo de sexta contava 0 dia útil de atraso.
- O que mudou: entrega depois do prazo conta pelo menos 1 dia de atraso (suposição S-cal-1, com teste). O cliente que esperava na sexta percebe o atraso.
- Antes → depois: N22 157 → 147 (30% dos atrasos).

## 2026-11-05 18:43: erro da IA (priorização)
- O que aconteceu: a skill de negócio, escrita pelo Claude Code, dizia que ordenar pelo custo de espera de amanhã e pegar os 150 primeiros era ótimo.
- Como percebemos: ao implementar o modelo. A tabela de cancelamento é em degraus, e um caso com 1 dia de atraso não piora amanhã, mas salta depois de amanhã. O guloso de um dia adia esse caso e paga o salto.
- O que mudou: a priorização virou um problema de atribuição casos × vagas por dia, resolvido de forma exata pelo algoritmo húngaro (`src/negocio/priorizacao.py`). O teste `test_otimo_olha_alem_de_amanha` cobre o contraexemplo, e a skill e o SPEC foram corrigidos.
- Resultado: perda esperada FIFO R$ 118.043 → otimizado R$ 99.868 (N70, N71); maior risco hoje primeiro R$ 113.985 (N76).

## 2026-11-05 18:43: erro da IA (dupla contagem)
- O que aconteceu: o primeiro total de exceções evitáveis por mês somava o excesso dos padrões com todos os 147 atrasos falsos.
- Como percebemos: conferência de sobreposição. 79 dos 147 atrasos falsos já estavam dentro do padrão da Rota Express no Nordeste.
- O que mudou: entram só os 68 atrasos falsos que estão fora dos padrões.
- Antes → depois: N97 471 → 430 exceções/mês; N98 94 h → 86 h.

## 2026-11-05 18:46: erro da IA (exemplos do prompt)
- O que aconteceu: ao escrever os 4 exemplos do prompt de decisão, o Claude Code preencheu fatos de memória: prazo correto 01/10 (o certo é 30/09), receita de R$ 1.900 (é R$ 1.752,81), marcas erradas em 2 exemplos, "25 dias aberta" (são 43) e o padrão P06 ausente num caso que pertence a ele.
- Como percebemos: conferência de cada exemplo com `montar_ficha()` antes da primeira chamada ao modelo.
- O que mudou: os exemplos foram reescritos com os valores da ficha real. Regra daqui em diante: exemplo de prompt só entra depois de ser conferido contra a ficha gerada pelo código.

## 2026-11-05 18:46: decisão (modelo)
- A chave do Groq não tem Llama de chat disponível; os modelos de texto são openai/gpt-oss-120b, openai/gpt-oss-20b e qwen/qwen3.8-27b.
- Escolhido: openai/gpt-oss-120b (o maior, com tool calling e modo JSON). Limites medidos nos cabeçalhos: 1.000 requisições/dia e 8.000 tokens/minuto. Isso define o desenho: ficha compacta, no máximo 3 ferramentas por caso e lote de 150 casos com cache.

## 2026-11-05 18:59: erro da IA (gabarito fácil demais)
- O que aconteceu: o primeiro eval deu 100% em tudo (ação 33/33, recall humano 4/4, padrão 11/11, JSON 33/33). A linha de base sem LLM fez 26/33.
- Como percebemos: nota máxima levantou a suspeita de que o gabarito só media se o modelo copia a tabela da política.
- O que mudou: o eval passou a checar também a mensagem ao cliente (`eval/mensagens.py`: assinatura da marca, jargão interno, datas e valores fora da ficha, pedido de foto, prazo correto), e entraram casos adversariais (`eval/adversariais.py`).

## 2026-11-05 18:59: erro da IA (mensagem do modelo, prompt v1)
- O que aconteceu: no GB7023422 (atraso dentro do SLA, aguardando o cliente), o modelo pediu "foto ou confirmação de endereço", que não se aplicam a atraso, e não informou o prazo correto.
- Como percebemos: checagem automática `nao_informou_prazo_correto` do eval de mensagens.
- O que mudou: prompt v2. A regra de "aguardando cliente" agora diz o que falta em cada tipo e proíbe pedir algo que o tipo não exige.
- Antes → depois: mensagens sem problema 31/32 (v1); a v2 é medida na próxima rodada.

## 2026-11-05 18:59: erro da IA (contradição nos dados)
- O que aconteceu: caso adversarial A2 (extravio marcado como entregue, sem data de entrega). O modelo mandou reenviar sem notar a contradição.
- Como percebemos: `eval/adversariais.py`, que deu 3/4. A injeção de instrução no nome do produto (A1) não funcionou, e o tipo fora da política (A3) foi para o humano por iniciativa do próprio modelo.
- O que mudou: checar consistência de dados é regra que não pode falhar, então foi para o código (H1 ampliada em `src/agente/regras.py`, com teste). Nos dados reais nada muda: continuam 32 casos em H1 (N04).

## 2026-11-05 19:08: resultado (prompt v2)
- Eval v2 (eval/resultados/2026-11-05_1907_v2.json): ação 33/33, recall humano 4/4, padrão 11/11, JSON na 1ª tentativa 33/33, mensagens sem problema 31/32 → 33/33. Linha de base sem LLM: 26/33.
- Adversariais: 3/4 → 4/4. A2 agora é pego pela H1 no código; A1 (injeção) e A3 (tipo fora da política) continuam corretos.
- Ressalva: o gabarito tem rótulos propostos pelo Claude Code a partir da política do SPEC e ainda aguarda a revisão do Levi.

## 2026-11-05 19:08: erro da IA (vazamento em mensagem de erro)
- O que aconteceu: no primeiro teste do link publicado, o erro 429 do Groq voltou cru para o navegador, com o id da organização da conta.
- Como percebemos: teste manual de POST /api/processar no link público, enquanto o lote consumia a cota.
- O que mudou: `src/agente/llm.py` devolve mensagens genéricas ("limite de uso do plano gratuito") e manda o detalhe só para o log do servidor. Uma busca por "org_" nos arquivos gerados não achou nada.

## 2026-11-05 19:08: decisão (deploy)
- Primeiro deploy na Vercel (mesa-de-excecoes.vercel.app): front estático + função Python só com fastapi, pydantic e groq. Pandas e scipy ficam fora da função; a fila, as decisões e os chamados vão como JSON gerado por `src/exportar.py`. Assim o link funciona mesmo com a cota do Groq esgotada.

## 2026-11-05 19:22: feedback (Levi)
- O Levi pediu que a interface seguisse a linguagem visual da página de talentos do Gogroup, para a banca reconhecer a "cara" do grupo.
- O que mudou: a captura de tela desse domínio foi bloqueada pela extensão, então os tokens saíram do CSS público da página (fundo #eef3fb com pontos, azul #2659a5, amarelo #d7d900 com sombra 3D #8e8f00, Poppins 800 e JetBrains Mono, painéis com cantos de 18 a 32 px, pílulas "Fase N", terminal escuro). Cada componente foi mapeado para o conteúdo do projeto: o terminal virou o registro do agente processando a fila, e os blocos coloridos viraram os números do dia. O logotipo do Gogroup não foi usado, e o rodapé diz que o projeto não é produto oficial.

## 2026-11-05 19:23: feedback (Levi)
- A persona deixou de se chamar Marina, porque o nome pode confundir com uma agente de IA que já existe no Gogroup. Primeiro troquei para Lívia, afirmando que o nome não aparecia nos dados. A conferência mostrou que a afirmação estava errada: "Lívia" aparece 5 vezes no case Atendimento, como nome pedido em capinhas personalizadas. O Levi escolheu Juliana, e a persona ficou Juliana (nome fictício). As entradas anteriores deste LOG não citavam o nome; a troca foi no SPEC, no README e na interface.

## 2026-11-05 20:03: mudança de rota (limite diário do modelo)
- O que aconteceu: o lote da fila do dia praticamente parou depois de 37 casos.
- Como percebemos: o Levi perguntou do progresso. A medição mostrou 1 decisão a cada 10 minutos e, numa chamada isolada, o erro 429 do Groq por tokens POR DIA (TPD): limite de 200.000 tokens, 199.304 usados. O limite por minuto (8.000) não era o problema.
- Conta: cada decisão gasta uns 3.000 tokens, o que dá cerca de 66 decisões por dia no plano gratuito. Eval v1 + eval v2 + adversariais + o início do lote consumiram a cota do dia.
- O que mudou: (1) o cliente desiste na hora quando o Groq manda esperar mais de 65 s, em vez de gastar uns 40 s insistindo à toa; (2) o lote ganhou o modo `--paciente`, que espera a janela liberar e continua, e no fim gera os chamados que faltarem; (3) a interface separa "na fila do agente" (sem decisão ainda) de "aguarda a Juliana" (decisão de mandar para a pessoa), porque antes os casos não processados inflavam o contador de revisão humana; (4) o README explica o limite e o que muda em produção.

## 2026-11-05 20:17: decisão (segundo modelo para a fila do dia)
- Contexto: o limite diário do gpt-oss-120b acabou (ver entrada anterior). O Levi escolheu usar também o openai/gpt-oss-20b, que tem cota própria de 200.000 tokens por dia.
- Correção de uma afirmação minha: eu tinha dito que, com o 20b, a fila terminaria no mesmo dia. A página de limites do Groq mostra o mesmo teto diário para os três modelos, então o 20b só adianta (eval + cerca de 33 casos hoje).
- Eval do 20b antes de usá-lo (eval/resultados/2026-11-05_2016_v2_gpt-oss-20b.json, sem sobrescrever o cache do 120b): recall humano 4/4, ação 31/33, mensagens 31/31, padrão 11/11, JSON na 1ª tentativa 32/33. Os 2 erros mandaram para a pessoa reenvios que podiam ser automáticos: o modelo leu "7 dias do recebimento" como dias desde a abertura do caso. É erro no sentido seguro e fica documentado; corrigir exigiria um prompt v3 e um novo eval nos dois modelos.
- O que mudou: cada decisão guarda o modelo que a tomou, e a tela mostra isso. O 20b processa a fila do começo e o 120b do fim, cada um com a sua cota.

## 2026-11-05 20:36: erro da IA (eval errado na tela)
- O que aconteceu: a exportação pegava o resultado de eval mais recente, que passou a ser o do gpt-oss-20b, e a seção "Como sabemos" do site mostrava esse eval como se fosse o principal.
- Como percebemos: conferência do eval.json depois do deploy.
- O que mudou: `src/exportar.py` usa só o eval do modelo principal, porque arquivos de outros modelos levam o nome do modelo no fim. A tela voltou a mostrar 2026-11-05_1907_v2.json (120b).

## 2026-11-06 09:23: resultado (fila do dia completa)
- Com a cota recarregada durante a noite, os dois lotes fecharam a fila: 150/150 decisões (gpt-oss-120b: 79, gpt-oss-20b: 71) e os 7 chamados de causa raiz. Nenhum limite diário foi atingido hoje.
- Conferência automática contra a tabela de política (analises/a06_fila_do_dia.py): 145/150 decisões batem (N101), 148/149 mensagens sem problema (N103), 3 casos para a analista (N102). Das 5 divergências, 3 são a confusão dos "7 dias" já registrada, 1 é o GC7021341 (o 20b cobrou a transportadora num atraso dentro do SLA) e 1 é um rastreio parado aguardando o cliente (o 120b cobrou a transportadora em vez de lembrar o cliente).

## 2026-11-06 09:23: erro da IA (auditor de números)
- O que aconteceu: `eval/auditar_numeros.py` só reconhecia ids de 2 dígitos. As citações N100 a N103 passavam sem conferência, e "[N100]" era lido como N10, outro número.
- Como percebemos: o auditor contou 47 citações depois de 4 novas entrarem no README.
- O que mudou: o regex aceita ids de 2 e 3 dígitos; agora são 51 citações conferidas, todas batendo.

## 2026-11-06 09:23: erro da IA (monitor dos lotes)
- O que aconteceu: o monitor do lote declarou "lotes encerrados" quando eles ainda estavam rodando. No Git Bash do Windows, `ps` não mostra os argumentos do processo, então a checagem pelo nome do módulo falhava.
- O que mudou: o fim do lote passou a ser detectado pela linha final do log.

## 2026-11-06 10:01: feedback (avaliador cego)
- O avaliador cego (`.claude/agents/recrutador-gogroup.md`), que só via o link, o repositório e o enunciado, deu 7,2/10 e "avançaria para entrevista com ressalvas". As três críticas mais graves foram conferidas e procedem.
- Ferramentas só declaradas: 0 chamadas em 182 decisões. O README passou a dizer isso e por quê (a ficha já traz o que o modelo precisa).
- Régua circular: o gabarito foi proposto pela própria tabela de política, que acerta 33/33 sem modelo. O eval agora mostra essa linha de base ao lado da ação fixa por tipo (26/33), e o README separa o que é do código (casos de risco, padrões) do que é do modelo (mensagem, casos fora da tabela, injeção).
- Erro do modelo que o checador deixou passar: no GB7000254 o gpt-oss-20b escreveu "Você não precisa enviar foto" e o reenvio saiu automático. O checador só procurava a palavra "foto". O que mudou: o checador detecta a dispensa da foto; a nova regra H7 manda para a analista todo reenvio cuja mensagem não pede a foto; e o reenvio que depende de foto fica "aguardando a foto do cliente". Antes → depois: N103 148 → 147 de 149.
- Reenvio sem teto: 52 reenvios automáticos no dia. Nova regra H2b: reenvio acima do percentil 95 do custo (R$ 73,21, N68) vai para a analista. A primeira versão pegava por engano uma devolução, cujo custo é só o frete (S5), e foi corrigida. Efeito na fila: 5 casos para a analista por H2b e 1 por H7; N102 3 → 9. No gabarito, o GB7022256 passou a "deve ir para humano" (H2b); recall humano 5/5.
- O ganho de R$ 18.175 é de uma vez, sobre o estoque acumulado; o README agora diz isso e o que seria o ganho recorrente.
- Chamados de causa raiz: a evidência passou a ir ao modelo com nomes legíveis e com o dado específico de cada padrão (brinde no CD2, dias além do SLA na transportadora). Prompt v2 → v3. O modelo errou no P00 (chamou de "geradas pela regra" as 497 exceções de atraso, quando são 147) e inventou uma meta no P02. O v3 pede só a direção da meta e proíbe mudar o sentido dos números. No v3 o P02 deixou de citar o brinde, então a interface mostra a evidência calculada pelo código em cada chamado.
- Enunciado e dados: tirados do repositório e do histórico (ver próxima entrada).

## 2026-11-06 10:01: decisão (enunciado e dados fora do repositório)
- O que aconteceu: o PDF do enunciado e os CSVs estavam no repositório público, e o enunciado pede para não compartilhá-los. Eu tinha decidido versioná-los no começo; revi a decisão depois do avaliador cego.
- O que mudou: os dois saíram do repositório e de todo o histórico (`git filter-branch` + push forçado). Ficam só locais, no `.gitignore`. O README explica onde colocar os arquivos do desafio, e os testes que precisam deles são pulados com aviso.
- Erro da IA no caminho: a primeira reescrita do histórico (com `--all` e limpeza imediata) apagou do repositório local o commit das melhorias. Como percebemos: o `git log` mostrava o `main` no commit antigo. Recuperamos pelo backup feito antes (`git bundle`) e refizemos só na `main`, conferindo que a árvore final era idêntica. Nada errado chegou ao GitHub.

## 2026-11-06 10:36: feedback (avaliador cego, segunda rodada)
- Segunda avaliação cega: 7,2 → 7,8, mesmo veredito (avançaria com ressalvas), top 3 de 30. Corrigidas só as inconsistências apontadas, por decisão do Levi.
- Modelo de perda contava reembolso em pagamento pendente, de dinheiro que não entrou. Corrigido em `src/negocio/risco.py`, com teste. Antes → depois: N72 R$ 18.175 → R$ 17.448; N70 R$ 118.043 → R$ 112.698; N71 R$ 99.868 → R$ 95.249. A fila do dia mudou em 7 casos, decididos de novo (3 pelo 120b e 4 pelo 20b, porque o 120b atingiu o limite diário). Fila: 150/150.
- O chamado P01 dizia 3,6 dias além do SLA e o README 3,0 (N54), com definições diferentes. A evidência dos chamados agora usa a mesma definição de N54/N55, e o P01 foi gerado de novo (20b): 3,0. Ao gerar de novo o P03, o 20b escreveu "aumento de 29% de avarias" quando 29% é a proporção no grupo; mantivemos o texto anterior do 120b e só atualizamos a evidência calculada pelo código, que esse texto não cita. Os chamados registram o modelo.
- O README dizia que o auditor conferia a interface, mas ele só lia README e SPEC. Agora confere também web/public/data/numeros.json e os ids citados em web/src, além dos valores em negrito; com isso pegou 10 valores desatualizados depois da correção do modelo de perda.
- "141 resolvidos" misturava 40 reenvios que ainda esperam a foto. A tela agora diz "decididos sem a Juliana" e quantos deles esperam a foto, e o detalhe do caso mostra essa situação.
- O título dizia que o agente escolhe as 150 de hoje; quem escolhe é o algoritmo de otimização. Título e frase de abertura do README corrigidos. CLAUDE.md dizia "Llama"; agora diz gpt-oss.
- Gabarito: revisado caso a caso pelo Claude Code contra o texto do SPEC (marcado `claude_revisado`, não como revisão do Levi). Concordou com os 33 e apontou uma lacuna da política (rastreio parado há mais de 30 dias úteis).
- Não corrigido (fora do escopo pedido) e agora documentado no README: o furo da H7 com paráfrases e a linha de base "mais novo primeiro", que já chega perto do plano ótimo.

## 2026-11-06 10:38: decisão (gabarito)
- O Levi conferiu os 33 rótulos depois da revisão do Claude Code e confirmou todos. `anotado_por` passou de `claude_revisado` para `claude_revisado_por_levi`, e o README foi atualizado.

## 2026-11-06 11:05: decisão (modelo de reserva)
- Contexto: o link precisa continuar funcionando nas próximas semanas, e o Groq pode remover um modelo ou a cota do dia pode acabar.
- O que mudou: `src/agente/llm.py` tenta `openai/gpt-oss-120b` → `openai/gpt-oss-20b` → `qwen/qwen3.8-27b`. Passa ao próximo em limite de uso (429), modelo fora do ar (5xx), modelo removido ou inexistente (400/403/404 que citam o modelo) e tempo esgotado duas vezes. Erro do próprio pedido ou chave inválida não troca de modelo, porque outro modelo falharia igual. Depois de uma troca, a decisão inteira fica no mesmo modelo. O rastro registra a troca e o resultado grava o modelo que respondeu; a API publicada espera no máximo 10 s por modelo e não espera a cota liberar.
- Conferido antes: a listagem de modelos da conta (que não gasta cota) mostra os três. O qwen recebe os mesmos parâmetros menos o `reasoning_effort`, que é da família gpt-oss, e um bloco `<think>` na resposta é descartado antes de validar o JSON.
- O qwen não passou pelo eval. Se ele responder, a tela mostra o nome do modelo.
- Verificação: 11 testes novos em `tests/test_llm.py` simulam os erros do SDK sem rede; `python -m pytest`: 55 passed antes, 66 depois.

## 2026-11-06 11:05: números novos
- N104: 142 casos da fila do dia decididos sem a analista (N100 − N102). N105: 28,4 h de trabalho do time por dia que viram revisão (N104 × 12 min ÷ 60, estimativa: supõe que conferir é bem mais rápido que decidir, e isso não foi medido). N99: 7 mudanças de processo com dono (6 padrões + prazo do checkout). Entram no novo bloco de impacto da página.
- Erro meu no caminho: a primeira definição do N105 falava em horas "da analista"; 28,4 h por dia só existem somadas no time (150 × 12 min = 30 h).

## 2026-11-06 12:10: mudança de rota (página e identidade visual)
- Contexto: o Levi pediu que quem abre o link entenda em 10 segundos o problema, o que a solução faz e o impacto, e que o visual deixe de copiar a página de talentos do Gogroup (mesmas fontes, mesmo azul e amarelo, fundo pontilhado, botão com sombra 3D, terminal "mesa.run").
- O que mudou na página: quatro blocos antes da fila. (1) o problema em uma frase com N01, N05 e N70; (2) impacto com quatro números (N72, N104 de N100 com N105, N97 com N99, N23), cada um com "Como calculamos", um botão que abre a definição do registro e funciona no toque; (3) tabela antes e depois; (4) como sabemos, com as limitações em uma linha e o link para o README. O terminal saiu. Na tela, códigos internos viraram linguagem de negócio: "H2b" vira "Reenvio caro", com a regra como detalhe; "P01" vira "Rota Express no Nordeste".
- Visual: Manrope no texto, IBM Plex Mono só nos números, servidas com o site (@fontsource, sem Google Fonts). Marinho #0b1f3a, azul #1d5bd8, lima #c5e83a só nos números de ganho sobre o marinho. Contraste conferido por script: o menor é 5,14:1 (azul sobre o fundo azul-claro), acima do mínimo AA de 4,5:1. Fundo liso, botões planos, cantos de 6 px. O rodapé diz que é projeto de candidato e não produto oficial.
- "Rodar o agente agora": tempo limite de 25 s (AbortController). Em qualquer falha, a tela diz que mostra a decisão gravada. Testado no preview local: sem API aparece "a API respondeu com erro 502"; com uma API simulada que não responde, o aviso dos 25 s aparece e o botão volta ao normal.
- Erros meus no caminho, achados na conferência visual: os balões de definição apareciam abertos, porque o `display: grid` do CSS anulava o atributo `hidden`; a manchete dizia "2.000 pedidos com problema", mas o N01 conta exceções (pedido + tipo); no celular, o detalhe do caso ficava abaixo de uma lista longa, e agora a página rola até ele.
- Revisões: a revisão de diretrizes de interface apontou a falta de `<h1>`, um `theme-color` diferente do fundo, um `textarea` sem `name`, a falta de "Desfazer" depois de aprovar ou rejeitar e a lista de 150 itens sem `content-visibility`, e tudo foi corrigido. A kill-ai-slop apontou o desfoque do menu, que saiu. Ficaram três marcações de propósito: o sublinhado pontilhado indica que o número tem definição, "Como calculamos" é um botão com cara de link e a manchete em frase inteira foi pedida.

## 2026-11-06 12:35: verificação do deploy
- Link publicado: `/`, `/data/fila.json`, `/data/numeros.json` e `/api/saude` respondem 200. A saúde mostra o modelo principal, os dois de reserva e a chave configurada. A página não carrega nada do Google Fonts.
- Uma chamada ao vivo pelo botão (GC7022899): respondeu em 2 s pelo gpt-oss-120b, com a mesma ação da decisão gravada (cobrar a transportadora). Foi a única chamada ao modelo nesta rodada; os testes do fallback não usam rede.
