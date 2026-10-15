import type { Data } from "../data";

const url = (id: string) => `https://www.dgsi.pt/jstj.nsf/x/${id}?OpenDocument`;

export const fixture: Data = {
  meta: {
    taxonomy_version: "v1",
    prompt_version: "classify_v1",
    subset_size: 813,
    classified: 2,
    by_source: { sumario: 2 },
    quotes_rejected: 0,
    divergences_shown: 1,
    divergences_hidden: 0,
    divergences_unjudged: 0,
  },
  questions: [
    {
      id: "q6",
      title: "Prazo do contrato prometido",
      description: "Absoluto ou relativo?",
      split: "test",
      positions: [
        { id: "relativo", label: "Relativo", definition: "Def relativo." },
        { id: "absoluto", label: "Absoluto", definition: "Def absoluto." },
      ],
      counts: { relativo: 1, absoluto: 1 },
      first_year: 2010,
      last_year: 2011,
    },
  ],
  judgments: [
    {
      doc_id: "a",
      processo: "1/10",
      date: "2010-03-01",
      url: url("a"),
      secao: "",
      relator: "",
      question_id: "q6",
      position: "relativo",
      quote: "<b>O prazo é relativo</b>",
      text_source: "sumario",
      uniformizacao: false,
    },
    {
      doc_id: "b",
      processo: "2/11",
      date: "2011-03-01",
      url: url("b"),
      secao: "",
      relator: "",
      question_id: "q6",
      position: "absoluto",
      quote: "O prazo é absoluto",
      text_source: "sumario",
      uniformizacao: false,
    },
  ],
  divergences: [
    {
      id: "q6-split-2009-2012",
      question_id: "q6",
      type: "split",
      window_start: 2009,
      window_end: 2012,
      display: "mudanca",
      rule_confidence: "media",
      support: { relativo: 2, absoluto: 2 },
      pair: [
        { doc_id: "a", processo: "1/10", date: "2010-03-01", url: url("a"), position: "relativo", quote: "O prazo é relativo" },
        { doc_id: "b", processo: "2/11", date: "2011-03-01", url: url("b"), position: "absoluto", quote: "O prazo é absoluto" },
      ],
      judge: { real_opposition: true, legislative_change_possible: false, rationale: "r", confidence: "media" },
    },
  ],
  aujs: [
    {
      id: "auj-2019",
      doc_id: "u",
      processo: "9/19-A",
      date: "2019-02-12",
      url: url("u"),
      related_questions: ["q6"],
      question_quote: null,
      conflict_quote: "Os acórdãos decidiram em sentido oposto",
      sides: [
        {
          auj_quote: "interpretação restrita",
          judgments: [{ doc_id: "a", processo: "1/10", date: "2010-03-01", url: url("a"), quote: "<i>Só o uso privado</i>" }],
        },
        { auj_quote: "interpretação ampla", judgments: [] },
      ],
      ruling_quote: "Uniformiza-se assim",
    },
  ],
  evaluation: {
    cost: { input_tokens: 1000, output_tokens: 200, usd_estimate: 0.5 },
    grounding: { proposed: 10, accepted: 9, rejected: 1 },
    position: [
      { set: "test", system: "model", rows: 4, unclear: 0, exact: [3, 4], recall: [2, 2], precision: [2, 3] },
      { set: "test", system: "baseline", rows: 4, unclear: 0, exact: [2, 4], recall: [0, 2], precision: [0, 0] },
    ],
    divergences: { judged: 5, shown_v1: 1, shown_v2: 2, shown_v2_test: 2 },
    aujs: 1,
    divergence_labels: null,
    survey: [{ seed: 5, topic: "Sinal e execução específica", question: "q10", result: "sim" }],
  },
};

export const empty: Data = {
  ...fixture,
  meta: { ...fixture.meta, classified: 0, divergences_shown: 0 },
  questions: fixture.questions.map((q) => ({ ...q, counts: {}, first_year: null, last_year: null })),
  judgments: [],
  divergences: [],
  aujs: [],
  evaluation: null,
};
