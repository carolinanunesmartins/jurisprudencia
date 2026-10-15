# Avaliação

Gerado por `make evaluate` a partir dos dados publicados no repositório. Contagens ao lado de cada percentagem; com amostras deste tamanho não se indicam intervalos de confiança. Afinação só nas perguntas de desenvolvimento (q2, q3); os resultados de teste são q6–q10.

## 1. Dados e custo

- Subconjunto: 813 acórdãos do STJ sobre contrato-promessa (2000–2025), todos classificados (100 no piloto e 713 na execução completa).
- Classificador `claude-haiku-4-5-20251001`: 1 607 043 tokens de entrada e 474 755 de saída (≈ 2 561 por acórdão). Custo estimado ≈ 3,98 USD a preços de tabela assumidos (1 / 5 USD por milhão; confirmar na consola).
- Juiz `claude-sonnet-5-5`: pair rule v1: 23 chamadas, pair rule v2: 9 chamadas. Tokens do juiz não registados.
- Tempo por etapa: não registado.

## 2. Citações (regra de verificação)

- Respostas com posição propostas pelo modelo: 695; aceites 684, rejeitadas 11. **Citações inventadas aceites: 0** (cada citação publicada é texto do próprio sumário, verificado).
- Como foram localizadas as aceites (uma citação pode ter mais de uma): ellipsis 23, exact 577, numbering 25, punctuation 4, spacing 9, trimmed 41, typography 22.
- `ellipsis` e `trimmed` mostram só parte do que o modelo citou.

## 3. Exatidão da posição (60 etiquetas)

Etiquetas feitas por um modelo de IA (Claude Opus 5.5) a pedido do responsável, sem revisão humana, da mesma família do classificador: a concordância pode estar inflacionada (ver `data/eval/labeller.md`). Linhas `unclear` excluídas.

| Conjunto | Sistema | Concordância exata | Etiqueta com posição → mesma posição | Posição dada → etiqueta concorda |
|---|---|---|---|---|
| teste (q6–q10) (42; 2 unclear) | modelo | 33/42 (79 %) | 20/21 (95 %) | 20/28 (71 %) |
| teste (q6–q10) (42; 2 unclear) | base de palavras-chave | 24/42 (57 %) | 4/21 (19 %) | 4/6 (67 %) |
| dev (q2, q3) (16; 0 unclear) | modelo | 13/16 (81 %) | 6/8 (75 %) | 6/8 (75 %) |
| dev (q2, q3) (16; 0 unclear) | base de palavras-chave | 7/16 (44 %) | 0/8 (0 %) | 0/1 (0 %) |

Erros do modelo (etiqueta → modelo):

- teste (q6–q10): nao_decide → absoluto ×1; nao_decide → afastada ×1; nao_decide → detentor ×1; nao_decide → exige_consumidor ×1; nao_decide → possuidor ×1; nao_decide → relativo ×3; nao_exige → nao_decide ×1
- dev (q2, q3): basta_mora → exige_definitivo ×1; exige_definitivo → nao_decide ×1; nao_decide → exige_definitivo ×1

## 4. Divergências detetadas e confirmadas pelo juiz

Regra de pares v1 (vizinhos no tempo) e v2 (pré-registada: sem citações parciais, par mais próximo). O sítio usa v2; a Gate G3 foi decidida em v1.

| Pergunta | Tipo | Janela | v1 | v2 | Confiança da regra (v2) |
|---|---|---|---|---|---|
| q2 (dev) | split | 2000–2016 | oculta | oculta | baixa |
| q2 (dev) | split | 2019–2025 | oculta | oculta | baixa |
| q3 (dev) | split | 2002–2006 | **mostrada** | oculta | baixa |
| q6 | shift | 2000–2005 | oculta | oculta | baixa |
| q6 | split | 2000–2025 | oculta | oculta | baixa |
| q7 | shift | 2004–2009 | **mostrada** | **mostrada** | alta |
| q7 | shift | 2007–2012 | oculta | oculta | baixa |
| q7 | shift | 2016–2021 | oculta | oculta | baixa |
| q7 | split | 2000–2025 | oculta | oculta | baixa |
| q8 | shift | 2011–2017 | oculta | oculta | baixa |
| q8 | split | 2014–2024 | oculta | **mostrada** | alta |
| q9 | shift | 2002–2007 | oculta | oculta | baixa |
| q9 | shift | 2007–2012 | oculta | oculta | baixa |
| q9 | shift | 2010–2015 | oculta | oculta | baixa |
| q9 | shift | 2015–2020 | oculta | oculta | baixa |
| q9 | shift | 2018–2023 | oculta | oculta | baixa |
| q9 | split | 2013–2021 | **mostrada** | **mostrada** | alta |
| q10 | shift | 2000–2005 | oculta | oculta | baixa |
| q10 | shift | 2003–2008 | oculta | **mostrada** | alta |
| q10 | shift | 2007–2012 | oculta | oculta | baixa |
| q10 | shift | 2010–2015 | oculta | oculta | baixa |
| q10 | split | 2000–2006 | oculta | oculta | baixa |
| q10 | split | 2008–2013 | oculta | oculta | baixa |

v1: 3 de 23 mostradas, 2 em perguntas de teste.

v2: 4 de 23 mostradas, 4 em perguntas de teste.

Gate G3 (≥ 1 divergência confirmada numa pergunta de teste): **ficar** no contrato-promessa (v1: 2).

## 5. Divergências reconhecidas pelo STJ

3 acórdãos de uniformização no subconjunto, apresentados com citações literais verificadas (`/uniformizacoes`). Não dependem do classificador nem do juiz; a escolha dos excertos foi feita por um agente de IA, sem revisão jurídica.

## 6. Precisão das divergências

Etiquetado por: Claude Opus 5.5 (não cego: viu os veredictos do juiz); GitHub Copilot. **Não é a verificação humana prevista no SPEC §9.2**: são etiquetas de modelos de IA, a partir dos dois excertos, e devem ser lidas como tal. Só as divergências etiquetadas entram na contagem.

| Conjunto | correct | incorrect | legislative_change | unclear | correct / decididas |
|---|---|---|---|---|---|
| mostradas no sítio (4; Claude Opus 5.5) | 2 | 1 | 0 | 1 | 2/3 (67 %) |
| ocultadas pelo juiz (4; GitHub Copilot) | 1 | 3 | 0 | 0 | 1/4 (25 %) |

Nas mostradas, `correct` / decididas é a precisão; nas ocultadas, cada `correct` é uma divergência real que o juiz escondeu.

Decididas = correct + incorrect + legislative_change; `unclear` excluído.

Notas:
- q10 shift 2003-2008: «implica convenção contrária» vs «presunção relativa, iuris tantum, ilidível»: respostas opostas sobre a ilidibilidade.
- q7 shift 2004-2009: O excerto de 2006 refere a transferência da posse de passagem, sem dizer se é posse em nome próprio.
- q8 split 2014-2024: «depende da sua qualidade de consumidor» vs «não se exige… a qualidade de consumidor».
- q9 split 2013-2021: Fundamentos diferentes: subsistência do direito de retenção e execução vs oponibilidade da posse à hipoteca anterior.

## 7. Recuperação do inquérito (5 perguntas-semente)

| # | Tema | Pergunta | Resultado | Evidência |
|---|---|---|---|---|
| 1 | Execução específica e alienação a terceiro antes do registo da acção | — | não avaliável | Pergunta rejeitada na taxonomia (q1): só 1 acórdão na amostra de descoberta de 150. Os acórdãos de referência do inquérito (086931, 1998; 05B743, 2005) estão no índice mas sem texto no dgsi.pt. |
| 2 | Execução específica: mora ou incumprimento definitivo | q2 | parcial | Divisão detetada (2000–2016 e 2019–2025) e os acórdãos de 19/05/2010 e 09/12/2010 citados no inquérito estão classificados como «basta a mora»; o juiz não confirmou nenhum par, por isso não aparece no sítio. |
| 3 | Sinal e mora | q3 | parcial | Divisão 2002–2006 confirmada pelo juiz com a regra de pares v1 (2002: «exige incumprimento definitivo» vs «a mora basta»); com a regra v2 o par escolhido não toma posição e fica oculta. A posição minoritária tem só 3 acórdãos. |
| 4 | Redução equitativa da cláusula penal aplicada ao sinal | — | não avaliável | Pergunta rejeitada na taxonomia (q4): 0 acórdãos na amostra de descoberta de 150. |
| 5 | Presunção de afastamento da execução específica quando há sinal | q10 | sim | A pergunta-semente (q5) foi rejeitada (0 na amostra de descoberta), mas o mesmo tema é a pergunta descoberta q10. Mudança 2003–2008 confirmada (2004: o sinal «implica convenção contrária» vs 2006: «presunção relativa, iuris tantum»). O acórdão de 19/12/2006 (06B3805) citado no inquérito está classificado como «admissível», dentro dessa janela. |

## 8. Limitações

- Etiquetas de avaliação feitas por IA, da mesma família do classificador.
- Uma só fonte de verificação das divergências (o juiz, um modelo); sem jurista.
- Classificação a partir do sumário (ADR 0007): o que o sumário omite não é visto.
- O classificador atribui posição a acórdãos que só tocam a pergunta (ver erros na secção 3); o juiz filtra, ocultando também divergências reais.
- Subconjunto por descritor (ADR 0005); só 2000–2025.
