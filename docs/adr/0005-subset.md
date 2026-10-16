# ADR 0005 — Subconjunto: contrato-promessa, STJ, 2000–2025

Estado: aceite (2026-10-13). Os números vêm do crawl do índice completo (`make index`, 723 pedidos) e de `pipeline/tools/subset_counts.py`.

## Contexto
O SPEC §2 fixa a regra: tema *contrato-promessa*, escolhido pelos descritores do DGSI, anos 2000–2025, alvo de 600 a 1 500 acórdãos; se houver mais, restringir a 2005–2025; se houver menos de 400, alargar com "Sinal" e "Execução específica".

Factos do índice (2026-10-13): 71 760 acórdãos indexados (o SPEC §2 citava 73 682, a contagem do próprio sítio; a listagem tem menos 1 922, não investigado, e é ela o universo real deste projeto). De 1932 a 2026, com um arquivo escasso antes de 1967. Os descritores são texto livre com muitas grafias (`CONTRATO-PROMESSA`, `CONTRATO PROMESSA`, `CONTRATO - PROMESSA DE COMPRA E VENDA`, …).

## Decisão
Um acórdão entra no subconjunto quando a data está entre 2000 e 2025 e pelo menos um dos seus descritores nomeia um *contrato-promessa* (expressão regular em `pipeline/juris/db/subset.py`, aplicada ao descritor inteiro, sem acentos):
- contém `CONTRATO-PROMESSA` (também com espaço, ou ` - `), ou
- começa por `PROMESSA DE COMPRA`, `PROMESSA DE VENDA`, `PROMESSA UNILATERAL` ou `PROMESSA BILATERAL`.

Resultado: **813 acórdãos** (649 se fosse 2005–2025). Está dentro do alvo de 600 a 1 500, por isso não se aplica nem a restrição de anos nem o alargamento do SPEC §2. Mantêm-se todos os anos de 2000 a 2025.

Por ano: 2000:22, 2001:26, 2002:23, 2003:37, 2004:56, 2005:37, 2006:51, 2007:41, 2008:38, 2009:47, 2010:57, 2011:36, 2012:34, 2013:25, 2014:20, 2015:26, 2016:21, 2017:21, 2018:21, 2019:32, 2020:16, 2021:29, 2022:25, 2023:24, 2024:25, 2025:23.

`make fetch` só descarrega este subconjunto (o piloto é tirado dele, estratificado por ano). `--all-index` existe para exploração e não é usado pelo pipeline.

## Porque não procurar por pedaços de palavra
Procurar `SINAL`/`TRADIÇÃO`/`PROMESSA` dentro do descritor apanha `EXTRADIÇÃO` (267 casos), `CONTRADIÇÃO …`, `CARÁCTER SINALAGMÁTICO`, `PROMESSA DE CASAMENTO`, descritores de sinais de trânsito e semelhantes. Os padrões sobre o descritor inteiro evitam-nos; `test_subset.py` fixa as duas listas.

## Porquê 2000–2025, e uma limitação conhecida
O ano de início é uma escolha de âmbito herdada do SPEC §2, não vem dos dados (o índice tem mais acórdãos por ano antes de 2000, não menos). A pergunta-semente 1 cita como referência o acórdão uniformizador de 05/11/1998, que fica **fora** da janela, por isso o "antes" dessa mudança não está nos dados. Considerado e rejeitado pelo responsável (2026-10-14): 1995–2025 daria 1 144 acórdãos (813 + 331) e incluiria 1998. A limitação está no relatório; a pergunta 1 é julgada só pelo que cai em 2000–2025.

## Consequências
- **Cerca de 25 a 30 acórdãos por ano**, com uma descida para 16 em 2020. A deteção por janelas (M5) trabalha com contagens pequenas; os limiares do SPEC §6 aplicam-se como estão escritos e o sítio mostra as contagens de cada janela.
- **Custo:** 813 descargas ≈ 40 a 45 minutos de crawl educado, muito abaixo da estimativa antiga de 1 a 2 horas.
- **Limite de cobertura:** acórdãos que tratam uma promessa mas não têm esse descritor (ou nenhum) ficam de fora. É uma limitação declarada do método, não afinada depois.
- **Não incluídos:** os descritores `SINAL`, `EXECUÇÃO ESPECÍFICA`, `TRADIÇÃO DA COISA` e `CLÁUSULA PENAL` sozinhos (também aparecem fora da promessa). O alargamento do SPEC §2 (família `SINAL` exata e `EXECUÇÃO ESPECÍFICA`) acrescentaria só 34 acórdãos em 2000–2025 (847 em vez de 813), por isso não mudaria o quadro.
- O Gate G2 (fim do M3) e o *spike* do M1.5 continuam a decidir se este subconjunto tem posições distintas suficientes.
