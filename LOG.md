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
