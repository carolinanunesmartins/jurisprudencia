import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { messages } from "./messages.pt";
import { DgsiLink, fmtDate, H2, H3, Pos, SMALL, useTitle } from "./pages";
import { highlight, type JudgmentHit, type QueryTerm, type SearchIndex, type SearchResult } from "./search";

const PAGE = 50;
const t = messages.search;

/** The quote with the words that matched wrapped in <mark>; still plain text, never HTML. */
function Marked({ text, terms }: { text: string; terms: QueryTerm[] }) {
  return (
    <>
      {highlight(text, terms).map((s, i) => (s.hit ? <mark key={i}>{s.text}</mark> : <span key={i}>{s.text}</span>))}
    </>
  );
}

/** One short line: the fields the words were found in; "sumário (não publicado)" when that is the only place. */
function WhereLine({ h }: { h: JudgmentHit }) {
  const only = h.where.length === 1 && h.where[0] === "summary";
  const fields = h.where.map((w) => (only ? t.where.summaryOnly : t.where[w])).join(", ");
  return (
    <p className={`${SMALL} mt-1.5`} title={h.where.includes("summary") ? t.where.summaryHint : undefined}>
      {t.where.label} {fields}
    </p>
  );
}

const questionUrl = (id: string) => `/perguntas/${encodeURIComponent(id)}`;

function Judgment({ h, terms }: { h: JudgmentHit; terms: QueryTerm[] }) {
  const j = h.judgment;
  return (
    <li className="border-b border-rule py-5">
      <p className={`${SMALL} tabular`}>
        {fmtDate(j.date)}, <DgsiLink url={j.url}>{j.processo || messages.table.open}</DgsiLink>
      </p>
      <p className="mt-1">
        <Link to={questionUrl(h.question.id)} className="font-serif text-lg leading-snug">
          {h.question.title}
        </Link>
      </p>
      <p className="text-sm">
        <Pos q={h.question} id={j.position} />
      </p>
      <blockquote className="voice mt-2 max-w-[38rem]">
        «<Marked text={j.quote} terms={terms} />»
      </blockquote>
      <WhereLine h={h} />
    </li>
  );
}

function Results({ result }: { result: SearchResult }) {
  const [shown, setShown] = useState(PAGE);
  const { questions, judgments, terms } = result;
  if (questions.length === 0 && judgments.length === 0) return null; // the status line says so
  return (
    <>
      {questions.length > 0 && (
        <section className="mt-8">
          <h3 className={H3}>{t.questionsHeading}</h3>
          <ul className="mt-3 border-t border-rule">
            {questions.map(({ question }) => (
              <li key={question.id} className="border-b border-rule py-3">
                <Link to={questionUrl(question.id)} className="font-serif text-lg leading-snug">
                  {question.title}
                </Link>
                <p className={`${SMALL} mt-0.5`}>{question.description}</p>
              </li>
            ))}
          </ul>
        </section>
      )}
      {judgments.length > 0 && (
        <section className="mt-10">
          <h3 className={H3}>
            {t.judgmentsHeading}
          </h3>
          <ul className="mt-3 border-t border-rule">
            {judgments.slice(0, shown).map((h) => (
              <Judgment key={`${h.judgment.doc_id}-${h.question.id}`} h={h} terms={terms} />
            ))}
          </ul>
          {judgments.length > shown && (
            <p className="mt-5 flex items-baseline gap-4">
              <button
                type="button"
                onClick={() => setShown(shown + PAGE)}
                className="border border-ink rounded-[3px] px-3 py-1.5 text-sm font-semibold"
              >
                {t.showMore}
              </button>
              <span className={`${SMALL} tabular`}>{t.shownOf(shown, judgments.length)}</span>
            </p>
          )}
        </section>
      )}
    </>
  );
}

export function SearchPage({ getIndex }: { getIndex: () => Promise<SearchIndex> }) {
  useTitle(messages.titles.search);
  const [params] = useSearchParams();
  const query = params.get("q") ?? "";
  const active = query.trim() !== "";
  const [index, setIndex] = useState<SearchIndex | null>(null);
  const [failed, setFailed] = useState(false);

  // the sumário index (~1 MB) is fetched the first time a query is run, never before
  useEffect(() => {
    if (!active) return;
    let alive = true;
    getIndex().then(
      (i) => alive && setIndex(i),
      () => alive && setFailed(true),
    );
    return () => {
      alive = false;
    };
  }, [active, getIndex]);

  const result = useMemo(() => (index && active ? index.search(query) : null), [index, active, query]);

  const distinct = result ? new Set(result.judgments.map((h) => h.judgment.doc_id)).size : 0;
  let status = "";
  if (active && failed) status = messages.loadError;
  else if (active && !result) status = t.loading;
  else if (result) {
    status = result.judgments.length === 0 && result.questions.length === 0 ? t.noResults(query.trim()) : t.count(distinct);
  }

  return (
    <section>
      <h2 className={H2}>{t.heading}</h2>
      {!active && (
        <div className="mt-4 max-w-[38rem]">
          <p className="text-lg text-graphite">{t.helpIntro}</p>
          <p className="mt-4 text-sm font-semibold">{t.examplesLabel}</p>
          <ul className="mt-1 flex flex-wrap gap-x-6 gap-y-1">
            {t.examples.map((e) => (
              <li key={e}>
                <Link to={`/pesquisa?q=${encodeURIComponent(e)}`}>{e}</Link>
              </li>
            ))}
          </ul>
        </div>
      )}
      {/* always mounted, so screen readers announce loading, then the count or "no results" */}
      <p role="status" aria-live="polite" className={`mt-4 text-graphite tabular ${active ? "" : "sr-only"}`}>
        {status}
      </p>
      {active && index && !index.summaryAvailable && <p className={`${SMALL} mt-1`}>{t.noSummaryIndex}</p>}
      {active && result && <Results key={query} result={result} />}
    </section>
  );
}
