// All user-facing strings live here (AGENTS.md rule 10). Plain pt-PT: say what a thing is or
// does; no dashes inside sentences; caveats stay explicit.
export const messages = {
  appTitle: "Jurisprudência",
  tagline: "Onde o Supremo decidiu a mesma questão de duas maneiras.",
  disclaimer: "Sinal para revisão, não é parecer jurídico.",
  skip: "Saltar para o conteúdo",
  months: ["jan.", "fev.", "mar.", "abr.", "mai.", "jun.", "jul.", "ago.", "set.", "out.", "nov.", "dez."],
  nav: {
    label: "Navegação principal",
    questions: "Perguntas",
    aujs: "Uniformizações",
    method: "Método",
  },
  home: {
    lead: (subset: number) =>
      `${subset} acórdãos do Supremo Tribunal de Justiça sobre contrato-promessa, de 2000 a 2025, lidos pergunta a pergunta. Cada divergência mostra os dois acórdãos e as palavras exatas de cada um.`,
    heroCaption: "A divergência mais clara até agora",
    openHero: "Ver como foi detetada",
    questionsIntro: "Sete perguntas. Em cada linha, um ano: acima do eixo uma posição, abaixo a outra.",
    aujs: (n: number) =>
      `${n} divergências que o próprio Supremo reconheceu ao uniformizar jurisprudência.`,
    method: "Como funciona e o que foi medido",
  },
  method_page: {
    heading: "Método e avaliação",
    stepsHeading: "Como funciona",
    steps: [
      "Os acórdãos são os do Supremo sobre contrato-promessa publicados no dgsi.pt entre 2000 e 2025, escolhidos pelos descritores.",
      "Há sete perguntas jurídicas. Cada uma tem duas posições, escritas antes de qualquer acórdão ser classificado.",
      "Um modelo de linguagem lê o sumário de cada acórdão e diz que posição toma em cada pergunta, citando o excerto que a sustenta. O excerto que aparece aqui é sempre texto do próprio sumário, verificado palavra a palavra. Se o excerto não estiver no sumário, a resposta é descartada.",
      "Em janelas de 3 anos, o sistema procura divisões (as duas posições com pelo menos 2 acórdãos cada) e mudanças (a posição que dominava deixa de dominar).",
      "Um segundo modelo, o juiz, lê só a pergunta e os dois excertos, sem saber o que o primeiro decidiu, e diz se a oposição é real. Só aparecem as divergências que ele confirma.",
      "Os acórdãos de uniformização são divergências que o próprio Supremo reconheceu. Aparecem só com citações, sem passar por nenhum modelo.",
    ],
    numbersHeading: "O que foi medido",
    grounding: (p: number, a: number, r: number) =>
      `Citações: ${p} respostas com posição, ${a} aceites e ${r} rejeitadas por não estarem no texto. Nenhuma citação inventada é mostrada.`,
    accuracyHeading: "Posição atribuída, numa amostra de 60 acórdãos",
    accuracyNote:
      "As etiquetas de referência foram feitas por um modelo de IA, sem revisão humana, por isso a concordância pode estar inflacionada. A base é uma regra simples de palavras-chave, fixada antes de ser medida.",
    cols: {
      set: "Conjunto",
      system: "Sistema",
      exact: "Concordância",
      recall: "Posição da etiqueta encontrada",
      precision: "Posição dada correta",
    },
    set: { test: "teste", dev: "afinação" },
    system: { model: "modelo", baseline: "base" },
    divergences: (j: number, v1: number, v2: number, t: number) =>
      `Divergências: o juiz avaliou ${j} e confirmou ${v2}, ${t} delas em perguntas de teste. Com a primeira regra de escolha dos excertos confirmava ${v1}.`,
    // same arithmetic as report §6: `unclear` is left out of the denominator
    labels: (correct: number, decided: number, unclear: number, labellers: string) =>
      `As divergências mostradas foram revistas por modelos de IA, não por uma pessoa (${labellers}): ${correct} de ${decided} consideradas corretas` +
      (unclear ? `, ${unclear} sem conclusão.` : "."),
    noLabels: "As divergências mostradas ainda não foram revistas por uma pessoa.",
    aujs: (n: number) => `${n} divergências reconhecidas pelo próprio Supremo (acórdãos de uniformização).`,
    cost: (tokens: string, usd: string) =>
      `A classificação gastou ${tokens} tokens, cerca de ${usd} USD a preços de tabela.`,
    surveyHeading: "Comparação com um levantamento anterior",
    limitsHeading: "Limitações",
    limits: [
      "As etiquetas de avaliação foram feitas por IA, da mesma família do classificador.",
      "As divergências são confirmadas por um modelo, o juiz, e não por um jurista.",
      "A classificação usa o sumário. O que o sumário omite não é visto.",
      "O classificador às vezes dá posição a acórdãos que só tocam a pergunta. O juiz filtra esses casos, mas também esconde algumas divergências reais.",
      "Só entram acórdãos de 2000 a 2025 com os descritores escolhidos.",
    ],
    report: "Relatório completo de avaliação, no GitHub",
    reportUrl: "https://github.com/carolinanunesmartins/jurisprudencia/blob/main/data/eval/report.md",
    unavailable: "A avaliação ainda não foi publicada.",
  },
  auj: {
    heading: "Uniformizações",
    intro:
      "Um acórdão de uniformização só existe quando o Supremo reconhece que acórdãos seus decidiram a mesma questão de forma oposta. Aqui estão a questão, os dois lados e a decisão final. Tudo o que está entre aspas é citação literal, com ligação ao original.",
    title: (date: string, processo: string) => `Acórdão de uniformização de ${date}, processo ${processo}`,
    question: "A questão",
    conflict: "A divergência",
    side: (n: number) => `Lado ${n}`,
    named: "Acórdãos deste lado, citados pelo acórdão",
    noneNamed: "O acórdão atribui este lado a acórdãos das Relações e não cita nenhum do Supremo.",
    ruling: "Jurisprudência uniformizada",
    open: "Abrir o acórdão de uniformização no dgsi.pt",
    related: "O que o Supremo disse sobre este tema",
    count: (n: number) => `${n} acórdãos de uniformização no subconjunto.`,
  },
  loading: "A carregar os dados…",
  loadError: "Não foi possível carregar os dados. Recarregue a página.",
  noData: "Ainda não há classificações publicadas.",
  notFound: "Esta pergunta não existe.",
  questionsHeading: "Perguntas",
  judgmentsCount: (n: number) => (n === 1 ? "1 acórdão com posição" : `${n} acórdãos com posição`),
  years: (a: number, b: number) => (a === b ? `${a}` : `${a}–${b}`),
  divergencesCount: (n: number) => (n === 1 ? "1 divergência" : `${n} divergências`),
  back: "Todas as perguntas",
  positionsHeading: "As duas posições",
  above: "acima do eixo",
  below: "abaixo do eixo",
  timelineHeading: "Ano a ano",
  timelineLabel: (title: string) => `Acórdãos por ano e por posição: ${title}`,
  timelineNote: "Cada ponto é um acórdão. Um anel marca um acórdão de uniformização. A faixa clara marca uma divergência.",
  tableHeading: "Todos os acórdãos",
  table: {
    date: "Data",
    processo: "Processo",
    position: "Posição",
    quote: "Citação",
    link: "Original",
    open: "Abrir no dgsi.pt",
  },
  onlySummary: "do sumário",
  fromText: "do texto integral",
  uniformizacao: "uniformização",
  divergencesHeading: "Divergências",
  // the heading of a divergence says what kind it is; a split is not a change over time
  kind: {
    split: "Divisão da jurisprudência",
    shift: "Mudança de entendimento",
    resolved: "Acórdão de uniformização no período",
  },
  legislative: "O juiz admite que a diferença venha de uma alteração legislativa.",
  confidence: { alta: "confiança alta", media: "confiança média", baixa: "confiança baixa" },
  confidenceTitle: { alta: "Confiança alta.", media: "Confiança média.", baixa: "Confiança baixa." },
  noDivergences: "Nenhuma divergência confirmada nesta pergunta.",
  divergence: {
    detail: "Ver como foi detetada",
    notFound: "Esta divergência não existe.",
    backTo: (title: string) => title,
    how: "Como foi detetada",
    window: (a: number, b: number) => `Anos analisados: ${a} a ${b}.`,
    support: "Acórdãos com posição nesses anos:",
    rule: {
      split:
        "Divisão: nos mesmos 3 anos há pelo menos 2 acórdãos de cada posição. Mostram-se os dois acórdãos de posições opostas mais próximos no tempo, com citações completas.",
      shift:
        "Mudança: a posição que dominava 3 anos seguidos (pelo menos 60 % e 2 acórdãos) dá lugar a outra num período posterior. Mostram-se o último acórdão da posição antiga e o primeiro da nova.",
      resolved:
        "Há um acórdão de uniformização com posição nesta pergunta, dentro ou depois do período da divergência. Isso não quer dizer que a divergência tenha terminado. Veja as datas.",
    },
    judge: (confidence: string) =>
      `Um segundo modelo, o juiz, leu só a pergunta, as posições e os dois excertos, sem saber que posição o classificador atribuiu. Concluiu que a oposição é real, com confiança ${confidence}.`,
    rationale: "Justificação do juiz, escrita por um modelo e não verificada:",
    ruleConfidence:
      "A confiança é alta quando o juiz confirma e a posição com menos acórdãos tem pelo menos 3, média com pelo menos 2, baixa nos outros casos.",
    judgeConfidence: { alta: "alta", media: "média", baixa: "baixa" },
  },
  splitTag: { dev: "Pergunta de afinação", test: "Pergunta de teste" },
} as const;
