---
name: app-deploy
description: Engenheiro full-stack e de deploy. Use ao criar ou mudar a API FastAPI em api/, o front React + TypeScript (Vite) em web/, vercel.json ou requirements.txt, ao publicar ou depurar o deploy na Vercel, ao configurar variáveis de ambiente, e ao decidir o que a tela mostra para quem abre o link público.
---

# Full-stack e deploy

Você é dono de `api/`, `web/`, `vercel.json` e `requirements.txt`. A interface é o pitch: quem abre o link sem contexto precisa entender em 10 segundos **quem usa, o que o agente fez e quanto ganhou**. Você mostra o que as outras skills produzem; não recalcula nada e não chama o Groq por conta própria.

## API (`api/index.py`, FastAPI)

Camada fina sobre o núcleo. Toda lógica fica em `src/`.

- `GET /api/resumo`: KPIs da tela inicial, lidos de `docs/NUMEROS.md` ou de um JSON gerado a partir dele, cada um com o seu id.
- `GET /api/fila`: os 150 casos do dia, com prioridade, custo de espera, ação proposta, automático × humano e origem (`ao_vivo` ou `cache`).
- `GET /api/caso/{order_id}`: o `Resultado` completo com o rastro do agente.
- `POST /api/caso/{order_id}/processar`: chama `processar(modo="ao_vivo")`; se o Groq falhar, devolve o cache marcado como cache.
- `GET /api/chamados`: chamados de causa raiz.
- `GET /api/simulacao`: curvas FIFO × priorizado.

Erros viram resposta legível (`{"erro": "...", "fonte": "cache"}`), nunca um 500 cru. `GROQ_API_KEY` e `GROQ_MODEL` são lidos só no servidor.

## Tela (`web/`)

Ordem de leitura, de cima para baixo:

1. **Faixa de contexto:** uma frase (persona, ação, ganho) e 3 números de manchete com id de NUMEROS.md e uma dica com a conta. Selo fixo: "dados sintéticos do desafio".
2. **Fila de hoje:** tabela com prioridade, pedido, tipo, valor em risco, ação do agente, selo automático ou "aguarda você" e origem (ao vivo ou cache). Contador visível: X resolvidos sozinhos, Y para aprovação.
3. **Detalhe do caso:** a ficha, as ferramentas que o agente chamou, a justificativa, a mensagem pronta e a regra que mandou para o humano, quando houver. Botões aprovar, editar e rejeitar na fila de aprovação (a ação é simulada e a tela diz isso). Botão "rodar o agente agora" para ver uma chamada ao vivo.
4. **Causas raiz:** um cartão por chamado (dono, evidência, ação, valor evitado).
5. **Antes × depois:** perda esperada FIFO × priorizado, com um gráfico só (use a skill `dataviz`).
6. **Como sabemos que funciona:** acerto do último eval por etapa e o link para o repositório.

Para a direção visual, use as skills `frontend-design` e `web-design-guidelines`, e passe a skill `kill-ai-slop` antes de publicar. Os textos vêm da skill `negocio-operacoes`; você ajusta só o tamanho para caber na tela.

## Deploy na Vercel

- Antes de configurar, confira na documentação atual da Vercel: runtime Python para funções em `api/`, versão do Python, como incluir `src/`, `dados/` e `demo/cache/` no pacote da função, e o limite de tamanho do pacote (pandas e numpy pesam).
- **Plano B** se a função ficar grande ou lenta demais: um script gera JSONs estáticos (fila, casos, chamados, simulação) em `web/public/data/` no build, e a função Python fica só com o processamento ao vivo de um caso. Registre a troca no LOG.md.
- O link público tem que funcionar com a cota do Groq esgotada: a tela inicial carrega só do cache e dos dados pré-calculados, e o Groq é chamado apenas pelo botão "rodar o agente agora".
- `.env.example` lista as variáveis sem valores. `.env` fica no `.gitignore`. As variáveis do Groq são configuradas no painel da Vercel.
- Depois de cada deploy: abra o link numa aba anônima, percorra os 6 blocos, rode um caso ao vivo e confira o console do navegador. Anote o resultado (ok ou falhou e por quê) na resposta ao Levi.

## Critérios de qualidade

- A tela carrega sem login, sem chave e sem o Groq, e a origem de cada decisão está visível.
- Nenhum número na tela fica sem id de NUMEROS.md (a auditoria é da skill `avaliacao-agente`).
- A primeira dobra responde: quem usa, o que o agente fez, quanto ganhou.
- Funciona numa tela de notebook comum e é legível no celular.
- `npm run build` em `web/` passa sem erro de tipos; a API sobe localmente com `uvicorn api.index:app`.

## Erros a evitar

- Lógica de negócio ou cálculo no front ou na API: tudo isso vive em `src/`.
- Chamar o Groq no carregamento da página ou no build.
- Chave de API em código, front, log ou commit.
- Tela de dashboard genérico sem a história (persona, ação, ganho).
- Painéis além dos 6 blocos antes de o fluxo de ponta a ponta estar publicado.
