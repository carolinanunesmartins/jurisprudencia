// Keyword search over questions, verified quotes and the sumário word index (search.json).
// Pure and synchronous: no React, no fetch. The normaliser is "v2" and must stay identical to
// pipeline/juris/search (shared golden file pipeline/tests/regression/golden/search_normalise.json).
import type { Judgment, Question, SearchFile } from "./data";

const MIN_LEN = 2; // shorter tokens are dropped unless all digits
const MAX_LEN = 30;
const NO_STOPWORDS: ReadonlySet<string> = new Set();

// BM25 (k1, b) and the weight of each field in the final score
const K1 = 1.2;
const B = 0.75;
const W = { title: 4, position: 3, description: 2, quote: 2, summary: 1 } as const;
const PREFIX_FACTOR = 0.8; // a prefix hit counts a little less than an exact one
const PREFIX_MIN = 3; // "possu" finds "possuidor", "po" finds nothing extra
const QUESTION_FACTOR = 0.25; // a judgment inherits only a little of its question's match
const PROCESSO_BOOST = 1000;
const TOP_QUESTIONS = 3;

/** No º/ª, NFKD, no combining marks, lowercase: "Execução" -> "execucao". */
// v2: º and ª separate words (442º = 442.º = 442); NFKD would turn them into "o" and "a"
const fold = (text: string) =>
  text.replace(/[ºª]/g, " ").normalize("NFKD").replace(/\p{M}/gu, "").toLowerCase();

export function normalise(text: string, stopwords: ReadonlySet<string> = NO_STOPWORDS): string[] {
  return (fold(text).match(/[a-z0-9]+/g) ?? []).filter(
    (t) => (t.length >= MIN_LEN || /^\d+$/.test(t)) && t.length <= MAX_LEN && !stopwords.has(t),
  );
}

const SEARCH_VERSION = 2; // the normaliser version the index was built with

/** search.json as published, or null if it is not the shape and version this code understands. */
export function validSearchFile(x: unknown): SearchFile | null {
  if (typeof x !== "object" || x === null) return null;
  const f = x as Partial<SearchFile>;
  if (f.version !== SEARCH_VERSION) return null;
  const { stopwords, docs, lengths, terms } = f;
  if (!Array.isArray(stopwords) || !stopwords.every((w) => typeof w === "string")) return null;
  if (!Array.isArray(docs) || !docs.every((d) => typeof d === "string")) return null;
  if (!Array.isArray(lengths) || lengths.length !== docs.length || !lengths.every((n) => Number.isFinite(n))) return null;
  if (typeof terms !== "object" || terms === null || Array.isArray(terms)) return null;
  for (const list of Object.values(terms)) {
    if (!Array.isArray(list)) return null;
    for (const e of list) {
      if (!Array.isArray(e) || e.length !== 2 || !Number.isInteger(e[0]) || e[0] < 0 || e[0] >= docs.length || !Number.isFinite(e[1])) {
        return null;
      }
    }
  }
  return f as SearchFile;
}

export type QueryTerm = { term: string; prefix: boolean };

/** The query's words; the last one is a prefix while it is being typed (>= 3 chars, no trailing space). */
export function parseQuery(query: string, stopwords: ReadonlySet<string> = NO_STOPWORDS): QueryTerm[] {
  const folded = fold(query);
  const typing = /[a-z0-9]$/.test(folded);
  const last = (folded.match(/[a-z0-9]+/g) ?? []).at(-1);
  const terms = new Map<string, boolean>();
  for (const term of normalise(query, stopwords)) {
    const prefix = typing && term === last && term.length >= PREFIX_MIN;
    terms.set(term, (terms.get(term) ?? false) || prefix);
  }
  return [...terms].map(([term, prefix]) => ({ term, prefix }));
}

export type Segment = { text: string; hit: boolean };

/** Splits `text` into runs, marking the words that match a query term (accent- and case-blind). */
export function highlight(text: string, terms: QueryTerm[]): Segment[] {
  // fold char by char so every folded char maps back to its span in the original text
  let norm = "";
  const starts: number[] = [];
  const ends: number[] = [];
  let at = 0;
  for (const ch of text) {
    const f = fold(ch);
    for (let k = 0; k < f.length; k++) {
      starts.push(at);
      ends.push(at + ch.length);
    }
    norm += f;
    at += ch.length;
  }
  const out: Segment[] = [];
  let cursor = 0;
  for (const m of norm.matchAll(/[a-z0-9]+/g)) {
    const tok = m[0];
    if (!terms.some((t) => tok === t.term || (t.prefix && tok.startsWith(t.term)))) continue;
    const from = starts[m.index];
    let to = ends[m.index + tok.length - 1];
    if (from === undefined || to === undefined) continue;
    // marks that follow the word ("fé" written as e + U+0301) belong inside the highlight
    for (let mark = /^\p{M}/u.exec(text.slice(to)); mark; mark = /^\p{M}/u.exec(text.slice(to))) to += mark[0].length;
    if (from > cursor) out.push({ text: text.slice(cursor, from), hit: false });
    out.push({ text: text.slice(from, to), hit: true });
    cursor = to;
  }
  if (cursor < text.length) out.push({ text: text.slice(cursor), hit: false });
  return out;
}

// ---------------------------------------------------------------------------------------------
// one field of one kind of entity (question titles, quotes, sumários ...), scored with BM25

type Postings = Map<string, [number, number][]>; // term -> [entity, term frequency]

class Field {
  private readonly avg: number;
  private keys: string[] | null = null;

  constructor(
    private readonly n: number,
    private readonly lengths: number[],
    private readonly postings: Postings,
  ) {
    this.avg = lengths.reduce((a, b) => a + b, 0) / Math.max(1, lengths.length) || 1;
  }

  static fromTokens(docs: string[][]): Field {
    const postings: Postings = new Map();
    docs.forEach((tokens, entity) => {
      const tf = new Map<string, number>();
      for (const t of tokens) tf.set(t, (tf.get(t) ?? 0) + 1);
      for (const [t, n] of tf) {
        const list = postings.get(t);
        if (list) list.push([entity, n]);
        else postings.set(t, [[entity, n]]);
      }
    });
    return new Field(docs.length, docs.map((d) => d.length), postings);
  }

  private expand({ term, prefix }: QueryTerm): [string, number][] {
    const out: [string, number][] = this.postings.has(term) ? [[term, 1]] : [];
    if (prefix) {
      this.keys ??= [...this.postings.keys()];
      for (const t of this.keys) if (t !== term && t.startsWith(term)) out.push([t, PREFIX_FACTOR]);
    }
    return out;
  }

  /** entity -> BM25 score of the term (the best of its exact and prefix forms). */
  score(q: QueryTerm): Map<number, number> {
    const best = new Map<number, number>();
    for (const [t, factor] of this.expand(q)) {
      const list = this.postings.get(t) ?? [];
      const idf = Math.log(1 + (this.n - list.length + 0.5) / (list.length + 0.5));
      for (const [entity, tf] of list) {
        const len = this.lengths[entity] ?? 0;
        const s = factor * idf * ((tf * (K1 + 1)) / (tf + K1 * (1 - B + (B * len) / this.avg)));
        if (s > (best.get(entity) ?? 0)) best.set(entity, s);
      }
    }
    return best;
  }
}

// ---------------------------------------------------------------------------------------------
// the index

export type Where = "quote" | "summary" | "question" | "processo";

export type QuestionHit = { question: Question; score: number };
export type JudgmentHit = { judgment: Judgment; question: Question; score: number; where: Where[] };

export type SearchResult = {
  terms: QueryTerm[];
  questions: QuestionHit[];
  judgments: JudgmentHit[];
};

export type SearchIndex = {
  /** false when search.json could not be loaded: only questions and quotes are searched. */
  summaryAvailable: boolean;
  stopwords: ReadonlySet<string>;
  search(query: string): SearchResult;
};

type Row = { judgment: Judgment; question: Question; qi: number; doc: number | undefined };

const byDate = (a: Judgment, b: Judgment) =>
  b.date.localeCompare(a.date) || a.doc_id.localeCompare(b.doc_id) || a.question_id.localeCompare(b.question_id);

export function createIndex(
  data: { questions: Question[]; judgments: Judgment[] },
  summary: SearchFile | null,
): SearchIndex {
  const stopwords: ReadonlySet<string> = new Set(summary?.stopwords ?? []);
  const norm = (s: string) => normalise(s, stopwords);
  const { questions } = data;

  const title = Field.fromTokens(questions.map((q) => norm(q.title)));
  const position = Field.fromTokens(questions.map((q) => norm(q.positions.map((p) => p.label).join(" "))));
  const description = Field.fromTokens(
    questions.map((q) => norm([q.description, ...q.positions.map((p) => p.definition)].join(" "))),
  );

  const qIndex = new Map(questions.map((q, i) => [q.id, i]));
  const docIndex = new Map((summary?.docs ?? []).map((id, i) => [id, i]));
  const rows: Row[] = [];
  for (const judgment of data.judgments) {
    const qi = qIndex.get(judgment.question_id);
    const question = qi === undefined ? undefined : questions[qi];
    if (qi !== undefined && question) rows.push({ judgment, question, qi, doc: docIndex.get(judgment.doc_id) });
  }
  const quote = Field.fromTokens(rows.map((r) => norm(r.judgment.quote)));

  let sumario: Field | null = null;
  if (summary) {
    sumario = new Field(summary.docs.length, summary.lengths, new Map(Object.entries(summary.terms)));
  }

  const rowsOfQuestion = new Map<number, number[]>();
  const rowsOfDoc = new Map<number, number[]>();
  const rowsOfProcesso = new Map<string, number[]>();
  const push = <K>(m: Map<K, number[]>, k: K, v: number) => {
    const list = m.get(k);
    if (list) list.push(v);
    else m.set(k, [v]);
  };
  rows.forEach((r, i) => {
    push(rowsOfQuestion, r.qi, i);
    if (r.doc !== undefined) push(rowsOfDoc, r.doc, i);
    const key = norm(r.judgment.processo).join(" ");
    if (key) push(rowsOfProcesso, key, i);
  });

  function search(query: string): SearchResult {
    const terms = parseQuery(query, stopwords);
    if (terms.length === 0) return { terms, questions: [], judgments: [] };
    const n = terms.length;

    // per term: entity -> weighted score, in each field
    const sTitle = terms.map((t) => title.score(t));
    const sPos = terms.map((t) => position.score(t));
    const sDesc = terms.map((t) => description.score(t));
    const sQuote = terms.map((t) => quote.score(t));
    const sSum = terms.map((t) => sumario?.score(t) ?? new Map<number, number>());

    // a question's score for term i
    const ofQuestion = (qi: number, i: number) =>
      W.title * (sTitle[i]?.get(qi) ?? 0) + W.position * (sPos[i]?.get(qi) ?? 0) + W.description * (sDesc[i]?.get(qi) ?? 0);

    const questionHits: (QuestionHit & { matched: number; index: number })[] = [];
    const candidates = new Set<number>();
    for (const m of [...sTitle, ...sPos, ...sDesc]) for (const qi of m.keys()) candidates.add(qi);
    for (const qi of candidates) {
      const question = questions[qi];
      if (!question) continue;
      let score = 0;
      let matched = 0;
      for (let i = 0; i < n; i++) {
        const s = ofQuestion(qi, i);
        if (s > 0) matched++;
        score += s;
      }
      questionHits.push({ question, score, matched, index: qi });
    }
    questionHits.sort((a, b) => b.matched - a.matched || b.score - a.score || a.index - b.index);

    // judgments: every row that any field touches
    const rowSet = new Set<number>();
    for (const m of sQuote) for (const r of m.keys()) rowSet.add(r);
    for (const m of sSum) for (const d of m.keys()) for (const r of rowsOfDoc.get(d) ?? []) rowSet.add(r);
    for (const qi of candidates) for (const r of rowsOfQuestion.get(qi) ?? []) rowSet.add(r);
    // the processo is matched on every token, repeats included ("g1 g1"), not on the deduplicated terms
    const processo = rowsOfProcesso.get(norm(query).join(" ")) ?? [];
    for (const r of processo) rowSet.add(r);
    const processoRows = new Set(processo);

    const hits: (JudgmentHit & { matched: number })[] = [];
    for (const r of rowSet) {
      const row = rows[r];
      if (!row) continue;
      const where = new Set<Where>();
      let score = 0;
      let matched = 0;
      for (let i = 0; i < n; i++) {
        const q = W.quote * (sQuote[i]?.get(r) ?? 0);
        const s = W.summary * (row.doc === undefined ? 0 : (sSum[i]?.get(row.doc) ?? 0));
        const p = QUESTION_FACTOR * ofQuestion(row.qi, i);
        if (q > 0) where.add("quote");
        if (s > 0) where.add("summary");
        if (p > 0) where.add("question");
        if (q + s + p > 0) matched++;
        score += q + s + p;
      }
      if (processoRows.has(r)) {
        where.add("processo");
        matched = n;
        score += PROCESSO_BOOST;
      }
      const order: Where[] = ["processo", "quote", "summary", "question"];
      hits.push({
        judgment: row.judgment,
        question: row.question,
        score,
        matched,
        where: order.filter((w) => where.has(w)),
      });
    }
    hits.sort((a, b) => b.matched - a.matched || b.score - a.score || byDate(a.judgment, b.judgment));

    return {
      terms,
      questions: questionHits.slice(0, TOP_QUESTIONS).map(({ question, score }) => ({ question, score })),
      judgments: hits.map((h) => ({ judgment: h.judgment, question: h.question, score: h.score, where: h.where })),
    };
  }

  return { summaryAvailable: summary !== null, stopwords, search };
}
