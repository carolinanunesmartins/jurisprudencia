// All user-facing strings live here (AGENTS.md rule 10). Plain, short pt-PT: the screen shows
// what matters; explanations sit behind a click. Sentences that need emphasis are split into
// parts so components can wrap a part in <strong> without any markup in this file.
export const messages = {
  appTitle: "Jurisprudência",
  pageTitle: (page: string) => `${page} | Jurisprudência`,
  homeTitle: "Jurisprudência: a mesma questão, decidida num sentido e no sentido oposto",
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
    // "A mesma questão, decidida [num sentido] e [no sentido oposto]."
    title: ["A mesma questão, decidida ", "num sentido", " e ", "no sentido oposto", "."],
    leadCount: (n: number) => `${n} acórdãos do Supremo`,
    leadMiddle: " sobre contrato-promessa, de 2000 a 2025, agrupados em ",
    leadQuestions: (n: number) => `${n} perguntas`,
    kindsLabel: "Dois tipos de divergência",
    kindDef: {
      shift: "uma posição substitui a outra",
      split: "as duas posições nos mesmos anos",
    },
    heroCaption: "Exemplo",
    divergencesHeading: "Divergências confirmadas",
    aujs: (n: number) => `${n} vezes o próprio Supremo reconheceu e resolveu uma divergência`,
    method: "Como funciona e o que foi medido",
  },
  method_page: {
    heading: "Método e avaliação",
    stepsHeading: "Como funciona",
    // [bold label, rest of the sentence]
    steps: [
      ["Recolha.", " Acórdãos do Supremo sobre contrato-promessa, publicados no dgsi.pt entre 2000 e 2025."],
      ["Perguntas.", " Cada pergunta jurídica tem duas posições, definidas antes de ler qualquer acórdão."],
      ["Classificação.", " Um modelo lê o sumário, escolhe a posição e cita o excerto. Só fica se a citação existir palavra a palavra."],
      ["Deteção.", " Em janelas de 3 anos procuram-se divisões e mudanças."],
      ["Confirmação.", " Um segundo modelo, o juiz, vê só os dois excertos e diz se a oposição é real. Só se mostram as confirmadas."],
      ["Uniformizações.", " Aparecem só com citações, sem passar por nenhum modelo."],
    ],
    numbersHeading: "O que foi medido",
    stats: {
      quotes: "citações verificadas palavra a palavra",
      quotesSub: (rejected: number) => `${rejected} rejeitadas. Nenhuma citação inventada é mostrada.`,
      divergences: "divergências confirmadas",
      divergencesSub: (judged: number) => `de ${judged} avaliadas pelo juiz.`,
      // the pair rule changed once (v1 -> v2); said plainly, behind the accuracy click
      pairRule: (v1: number, v2: number) =>
        `A regra que escolhe os dois excertos a comparar mudou uma vez. Com a primeira, o juiz confirmava ${v1} divergências; com a atual, que prefere excertos completos e próximos no tempo, confirma ${v2}.`,
      // same arithmetic as report §6: `unclear` is left out of the denominator
      labels: (correct: number, decided: number) => `${correct} de ${decided}`,
      labelsTitle: "divergências mostradas consideradas corretas",
      // the breakdown adds up to the shown total, so "2 de 3" next to "4" is not a contradiction
      labelsSub: (shown: number, correct: number, wrong: number, unclear: number, labellers: string) =>
        `Das ${shown} mostradas: ${correct} corretas, ${wrong} erradas, ${unclear} sem conclusão (não contam). Revistas por IA, não por uma pessoa: ${labellers}.`,
      noLabels: "As divergências mostradas ainda não foram revistas por uma pessoa.",
      aujs: "uniformizações do próprio Supremo",
      cost: (usd: string) => `${usd} USD`,
      costTitle: "custo da classificação",
      costSub: (tokens: string) => `${tokens} tokens, a preços de tabela.`,
    },
    accuracyHeading: "Precisão da posição atribuída (amostra de 60 acórdãos)",
    accuracyNote:
      "As etiquetas de referência foram feitas por IA, sem revisão humana: a concordância pode estar inflacionada. A base é uma regra de palavras-chave, fixada antes de ser medida.",
    cols: {
      set: "Conjunto",
      system: "Sistema",
      exact: "Concordância",
      recall: "Posição da etiqueta encontrada",
      precision: "Posição dada correta",
    },
    set: { test: "teste", dev: "afinação" },
    system: { model: "modelo", baseline: "base" },
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
    intro: "Quando o próprio Supremo reconheceu uma divergência e fixou a resposta.",
    processo: (p: string) => `processo ${p}`,
    question: "A questão",
    conflict: "A divergência",
    more: "A divergência e os dois lados",
    side: (n: number) => `Lado ${n}`,
    named: "Acórdãos deste lado, citados pelo acórdão",
    noneNamed: "O acórdão atribui este lado a acórdãos das Relações e não cita nenhum do Supremo.",
    ruling: "Jurisprudência uniformizada",
    open: "Abrir no dgsi.pt",
    related: "O que o Supremo uniformizou",
    about: "Sobre",
    showRuling: "Ler a jurisprudência uniformizada",
  },
  loading: "A carregar os dados…",
  loadError: "Não foi possível carregar os dados. Recarregue a página.",
  noData: "Ainda não há classificações publicadas.",
  notFound: "Esta pergunta não existe.",
  questionsHeading: "Perguntas",
  judgmentsCount: (n: number) => (n === 1 ? "1 acórdão" : `${n} acórdãos`),
  years: (a: number, b: number) => (a === b ? `${a}` : `${a}–${b}`),
  back: "Todas as perguntas",
  positionsHeading: "As duas posições",
  definitions: "O que quer dizer cada posição",
  above: "acima do eixo",
  below: "abaixo do eixo",
  timelineHeading: "Ano a ano",
  timelineLabel: (title: string) => `Acórdãos por ano e por posição: ${title}`,
  // the chart's symbol key
  legend: { dot: "um acórdão", ring: "uniformização", band: "anos de uma divergência" },
  timelineKey: "Legenda do gráfico",
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
    split: "Divisão",
    shift: "Mudança",
    resolved: "Uniformização no período",
  },
  // position labels are not quotes, so no «»; parts let the labels be coloured and bold
  direction: { from: "De ", to: " para ", both: " e ", same: " nos mesmos anos" },
  before: "Antes",
  after: "Depois",
  aujShort: (dates: string[]) =>
    `Uniformizada em ${dates.length === 1 ? dates[0] : `${dates.slice(0, -1).join(", ")} e ${dates[dates.length - 1]}`}.`,
  aujWhy:
    "Os acórdãos com a outra posição continuam a ser assinalados depois disso; o sistema não diz porquê.",
  // a shift says who dominated in two windows, not that the change lasted
  shiftScope: "Descreve só estes anos. O gráfico mostra o que veio depois.",
  legislative: "O juiz admite que a diferença venha de uma alteração legislativa.",
  noDivergences: "Nenhuma divergência confirmada nesta pergunta.",
  divergence: {
    detail: "Ver detalhes",
    notFound: "Esta divergência não existe.",
    toChart: "Ver o gráfico",
    evidence: "Acórdãos com posição",
    how: "Como foi detetada",
    rule: {
      split:
        "Divisão: nos mesmos 3 anos há pelo menos 2 acórdãos de cada posição. Mostram-se os dois acórdãos de posições opostas mais próximos no tempo.",
      shift:
        "Mudança: a posição que dominava 3 anos seguidos (pelo menos 60 % e 2 acórdãos) dá lugar a outra num período posterior. Mostram-se o último acórdão da posição antiga e o primeiro da nova.",
      resolved:
        "Há um acórdão de uniformização com posição nesta pergunta, dentro ou depois do período da divergência. Isso não quer dizer que a divergência tenha terminado.",
    },
    judge:
      "Um segundo modelo, o juiz, leu só a pergunta, as posições e os dois excertos, sem saber que posição o classificador atribuiu, e concluiu que a oposição é real.",
    rationale: "Justificação do juiz, escrita por um modelo e não verificada:",
    // two different confidences: the judge's own, and the detection's (judge + support)
    judgeConfidence: "Confiança do juiz",
    ruleConfidence: "Confiança da deteção",
    ruleConfidenceNote:
      "A confiança da deteção é alta quando o juiz confirma e a posição com menos acórdãos tem pelo menos 3, média com pelo menos 2, baixa nos outros casos.",
    level: { alta: "alta", media: "média", baixa: "baixa" },
  },
  titles: {
    questions: "Perguntas",
    aujs: "Uniformizações",
    method: "Método e avaliação",
  },
} as const;
