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
