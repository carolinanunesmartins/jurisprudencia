// Types of web/public/data/*.json; mirror of pipeline/juris/export/model.py (validated by data-check).

export type Meta = {
  taxonomy_version: string;
  prompt_version: string;
  subset_size: number;
  classified: number;
  by_source: Record<string, number>;
  quotes_rejected: number;
  divergences_shown: number;
  divergences_hidden: number;
  divergences_unjudged: number;
};

export type Position = { id: string; label: string; definition: string };

export type Question = {
  id: string;
  title: string;
  description: string;
  split: "dev" | "test";
  positions: Position[];
  counts: Record<string, number>;
  first_year: number | null;
  last_year: number | null;
};

export type Judgment = {
  doc_id: string;
  processo: string;
  date: string;
  url: string;
  secao: string;
  relator: string;
  question_id: string;
  position: string;
  quote: string;
  text_source: "sumario" | "texto";
  uniformizacao: boolean;
};

export type PairItem = {
  doc_id: string;
  processo: string;
  date: string;
  url: string;
  position: string;
  quote: string;
};

export type Divergence = {
  id: string;
  question_id: string;
  type: "split" | "shift" | "resolved";
  window_start: number;
  window_end: number;
  display: "mudanca" | "possivel_alteracao_legislativa" | "uniformizada";
  rule_confidence: "alta" | "media" | "baixa" | null;
  support: Record<string, number>;
  pair: PairItem[];
  judge: {
    real_opposition: boolean;
    legislative_change_possible: boolean;
    rationale: string;
    confidence: "alta" | "media" | "baixa";
  } | null;
};

// A divergence documented by the STJ itself (acórdão de uniformização); every text is a quote.
export type AujJudgment = { doc_id: string; processo: string; date: string; url: string; quote: string };

export type AujSide = { auj_quote: string; judgments: AujJudgment[] };

export type Auj = {
  id: string;
  doc_id: string;
  processo: string;
  date: string;
  url: string;
  related_questions: string[];
  question_quote: string | null;
  conflict_quote: string;
  sides: AujSide[];
  ruling_quote: string;
};

// Key numbers of data/eval/report.md (written by `make evaluate`); null when not published.
export type Score = {
  set: "test" | "dev";
  system: "model" | "baseline";
  rows: number;
  unclear: number;
  exact: [number, number];
  recall: [number, number];
  precision: [number, number];
};

export type Evaluation = {
  cost: { input_tokens: number; output_tokens: number; usd_estimate: number };
  grounding: { proposed: number; accepted: number; rejected: number };
  position: Score[];
  divergences: { judged: number; shown_v1: number; shown_v2: number; shown_v2_test: number };
  aujs: number;
  divergence_labels: Record<string, number> | null;
  survey: { seed: number; topic: string; question: string | null; result: string }[];
};

export type Data = {
  meta: Meta;
  questions: Question[];
  judgments: Judgment[];
  divergences: Divergence[];
  aujs: Auj[];
  evaluation: Evaluation | null;
};

async function getJson<T>(name: string): Promise<T> {
  // relative to the page: works with base "./", HashRouter and CSP connect-src 'self'
  const res = await fetch(`./data/${name}`);
  if (!res.ok) throw new Error(`${name}: HTTP ${res.status}`);
  return (await res.json()) as T;
}

export async function loadData(): Promise<Data> {
  const [meta, questions, judgments, divergences, aujs] = await Promise.all([
    getJson<Meta>("meta.json"),
    getJson<Question[]>("questions.json"),
    getJson<Judgment[]>("judgments.json"),
    getJson<Divergence[]>("divergences.json"),
    getJson<Auj[]>("aujs.json"),
  ]);
  const evaluation = await getJson<Evaluation>("evaluation.json").catch(() => null);
  return { meta, questions, judgments, divergences, aujs, evaluation };
}
