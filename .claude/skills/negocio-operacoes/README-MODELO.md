# Estrutura do README

O README faz o papel do pitch: a banca só vê o link e o repositório. Seções, nesta ordem:

1. **Frase de pitch** na primeira linha: "[Nome] é um agente de IA que [ação no fluxo], para que [persona] [resultado com número]".
2. **Links:** app publicado e como usar em 30 segundos (o que clicar primeiro).
3. **Problema:** a fila de hoje (volume, capacidade, dias de backlog) e quanto custa, com ids de `docs/NUMEROS.md`.
4. **O que o agente faz:** diagrama simples das etapas (ficha → investigação → decisão → regras → execução ou humano) e um caso real de cada lado: um resolvido sozinho e um que foi para a pessoa, com o motivo.
5. **Resultado:** acerto do eval por etapa (de `eval/resultados/`), casos automáticos × casos para o humano, e a diferença em R$ entre FIFO e priorizado.
6. **O que está causando as exceções:** tabela de recomendações de processo (dono, evidência, ação, valor evitado).
7. **Como a IA foi usada e conferida:** 3 a 5 episódios do LOG.md com antes e depois.
8. **Como rodar:** comandos copiados do ambiente real (requirements, scripts), não de memória.
9. **Com dados reais:** que fonte substitui cada CSV (OMS, ERP, API das transportadoras, CRM), o volume esperado, o arquivo a trocar (`src/dados/fonte.py`) e os cuidados (LGPD nos dados de cliente, permissões, limite de requisições do modelo).
10. **Limitações e próximos passos:** o que é simulado, o que falta para produção, o que faria com mais uma semana.

Regras de estilo: frases diretas, números com fonte, nada de adjetivo de vendedor. Dados sintéticos e persona fictícia aparecem declarados.
