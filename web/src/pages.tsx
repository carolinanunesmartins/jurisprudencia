import { type ReactNode, useEffect } from "react";
import { Link, useParams } from "react-router-dom";
import type { Auj, Data, Divergence, Judgment, Question, Score } from "./data";
import { messages } from "./messages.pt";
import { SearchBox } from "./SearchBox";
import { FIRST, LAST, MiniStrip, posColor, Timeline } from "./Timeline";

// ---------------------------------------------------------------------------------------------
// shared pieces
//
// Reading order on every page: what it is (bold, coloured by position), the two quotes, then
// everything that explains it behind a <More> click. Quotes are never styled inside.

/** "2019-10-29" -> "29 out. 2019" (browsers format pt-PT short dates as 29/10/2019). */
export function fmtDate(iso: string): string {
  const [y, m, d] = iso.split("-").map(Number);
  const month = m ? messages.months[m - 1] : undefined;
  return y && month && d ? `${d} ${month} ${y}` : iso;
}

/** Each route names itself in the tab and in search results (HashRouter shares one HTML page). */
export function useTitle(page?: string) {
  useEffect(() => {
    document.title = page ? messages.pageTitle(page) : messages.homeTitle;
  }, [page]);
}

function PageTitle({ title }: { title: string }) {
  useTitle(title);
  return null;
}

const labelOf = (q: Question, pos: string) => q.positions.find((p) => p.id === pos)?.label ?? pos;
const indexOf = (q: Question, pos: string) => q.positions.findIndex((p) => p.id === pos);

/** Confirmed by the judge and shown: what the home page and the question list count. */
const confirmed = (d: Divergence) => d.type !== "resolved" && d.judge?.real_opposition === true;

const divergenceUrl = (d: Divergence) => `/divergencias/${encodeURIComponent(d.id)}`;

const WINDOW = 3; // detection windows are 3 years (SPEC §6)

export const SECTION = "mt-16 first:mt-0";
export const H2 = "font-serif text-[1.75rem] leading-tight tracking-[-0.01em]";
export const H3 = "font-serif text-xl leading-snug";
export const SMALL = "text-sm text-graphite";
const MEASURE = "max-w-[38rem]";

// same rule as the publish gate (pipeline/juris/export/check.py SOURCE); repeated here so data
// that skipped the gate (local dev, a hand-edited file) can never become a javascript: link
const SOURCE = "https://www.dgsi.pt/";

export function DgsiLink({ url, children }: { url: string; children: ReactNode }) {
  if (!url.startsWith(SOURCE)) return <span className="tabular">{children}</span>;
  return (
    <a href={url} rel="noopener noreferrer" target="_blank" className="tabular">
      {children}
    </a>
  );
}

function Dot({ index }: { index: number }) {
  return (
    <span
      aria-hidden="true"
      className="inline-block size-2.5 rounded-full align-[0.05em] mr-1.5"
      style={{ background: posColor(index) }}
    />
  );
}

/** A position's name: bold and in its colour (weight is the non-colour cue, SPEC §8). */
export function Pos({ q, id }: { q: Question; id: string }) {
  const i = indexOf(q, id);
  return (
    <strong className="font-semibold" style={{ color: i >= 0 ? posColor(i) : undefined }}>
      {labelOf(q, id)}
    </strong>
  );
}

/** Mudança is a filled badge, Divisão an outlined one: told apart by shape, not by colour. */
function KindBadge({ type }: { type: Divergence["type"] }) {
  const look = type === "shift" ? "bg-ink text-paper border-ink" : "border-ink text-ink";
  return (
    <span
      className={`inline-block border rounded-[3px] px-1.5 py-px text-[0.7rem] font-semibold uppercase tracking-[0.08em] ${look}`}
    >
      {messages.kind[type]}
    </span>
  );
}

function KindYears({ d }: { d: Divergence }) {
  return (
    <span className="inline-flex items-center gap-2">
      <KindBadge type={d.type} />
      <span className="text-sm font-semibold tabular">{messages.years(d.window_start, d.window_end)}</span>
    </span>
  );
}

/** "De A para B" for a shift, "A e B nos mesmos anos" for a split; position names coloured. */
function Gist({ d, q }: { d: Divergence; q: Question }) {
  const [a, b] = d.pair;
  if (!a || !b) return null;
  const t = messages.direction;
  return d.type === "shift" ? (
    <>
      {t.from}
      <Pos q={q} id={a.position} />
      {t.to}
      <Pos q={q} id={b.position} />
    </>
  ) : (
    <>
      <Pos q={q} id={a.position} />
      {t.both}
      <Pos q={q} id={b.position} />
      {t.same}
    </>
  );
}

/** Anything that explains rather than shows: one click away, still in the DOM. */
function More({ label, children, className = "" }: { label: ReactNode; children: ReactNode; className?: string }) {
  return (
    <details className={`group ${className}`}>
      <summary className="inline-flex items-baseline gap-2 text-sm font-semibold py-1">
        <span aria-hidden="true" className="inline-block text-graphite transition-transform duration-200 group-open:rotate-90">
          ›
        </span>
        {label}
      </summary>
      <div className="mt-3 space-y-3">{children}</div>
    </details>
  );
}

type VoiceItem = {
  doc_id: string;
  stage?: string; // "Antes" / "Depois" on a shift
  index: number;
  label: string;
  date: string;
  processo: string;
  url: string;
  quote: string;
};

/** One judgment speaking: its position, its words, where to read it. */
function Voice({ v, large = false }: { v: VoiceItem; large?: boolean }) {
  const colour = v.index >= 0 ? posColor(v.index) : undefined;
  return (
    <article className="border-t-2 pt-3 flex flex-col gap-2.5" style={{ borderColor: colour ?? "var(--rule)" }}>
      <p className="text-sm">
        {v.stage && (
          <span className="mr-2 text-xs font-semibold uppercase tracking-[0.08em] text-graphite">{v.stage}</span>
        )}
        <strong className="font-semibold" style={{ color: colour }}>
          {v.label}
        </strong>
      </p>
      <blockquote className={`voice ${large ? "text-[1.25rem] leading-[1.5]" : ""}`}>«{v.quote}»</blockquote>
      <p className={`${SMALL} tabular`}>
        {fmtDate(v.date)}, <DgsiLink url={v.url}>{v.processo || messages.table.open}</DgsiLink>
      </p>
    </article>
  );
}

function VoicePair({ items, large = false }: { items: VoiceItem[]; large?: boolean }) {
  return (
    <div className="grid gap-8 sm:grid-cols-2 sm:gap-10">
      {items.map((v) => (
        <Voice key={v.doc_id} v={v} large={large} />
      ))}
    </div>
  );
}

function voices(d: Divergence, q: Question): VoiceItem[] {
  // a shift's pair is old position first (pipeline detect/core.py), so it reads before -> after
  const stages = d.type === "shift" ? [messages.before, messages.after] : [];
  return d.pair.map((p, i) => {
    const index = indexOf(q, p.position);
    return {
      doc_id: p.doc_id,
      stage: stages[i],
      index,
      label: q.positions[index]?.label ?? p.position,
      date: p.date,
      processo: p.processo,
      url: p.url,
      quote: p.quote,
    };
  });
}

/** Uniformizações dated inside a split's years: without a word, the split looks like it ignores them. */
function aujDatesIn(d: Divergence, aujs: Auj[]): string[] {
  if (d.type !== "split") return [];
  return aujs
    .filter((a) => {
      const y = Number(a.date.slice(0, 4));
      return y >= d.window_start && y <= d.window_end;
    })
    .map((a) => a.date)
    .sort()
    .map(fmtDate);
}

type Period = { when?: string; a: number; b: number; counts: [string, number][] };

function countsIn(q: Question, judgments: Judgment[], a: number, b: number): [string, number][] {
  const counts = new Map<string, number>(q.positions.map((p) => [p.id, 0]));
  for (const j of judgments) {
    const y = Number(j.date.slice(0, 4));
    if (j.question_id === q.id && y >= a && y <= b && counts.has(j.position)) {
      counts.set(j.position, (counts.get(j.position) ?? 0) + 1);
    }
  }
  return [...counts.entries()];
}

/** The pair's positions first, so the bars read in the headline's order ("De A para B"). */
function inPairOrder(d: Divergence, counts: [string, number][]): [string, number][] {
  const rank = (pos: string) => {
    const i = d.pair.findIndex((p) => p.position === pos);
    return i < 0 ? d.pair.length : i;
  };
  return [...counts].sort((x, y) => rank(x[0]) - rank(y[0]));
}

/** The evidence for a divergence: a shift compares its first and last 3-year windows; a split, its whole span. */
function periods(d: Divergence, q: Question, judgments: Judgment[]): Period[] {
  if (d.type !== "shift") {
    return [{ a: d.window_start, b: d.window_end, counts: inPairOrder(d, countsIn(q, judgments, d.window_start, d.window_end)) }];
  }
  const before = { when: messages.before, a: d.window_start, b: d.window_start + WINDOW - 1 };
  const after = { when: messages.after, a: d.window_end - WINDOW + 1, b: d.window_end };
  return [before, after].map((p) => ({ ...p, counts: inPairOrder(d, countsIn(q, judgments, p.a, p.b)) }));
}

/** Counts as bars: who dominated, readable at a glance. */
function Evidence({ d, q, judgments }: { d: Divergence; q: Question; judgments: Judgment[] }) {
  const ps = periods(d, q, judgments);
  const max = Math.max(1, ...ps.flatMap((p) => p.counts.map(([, n]) => n)));
  return (
    <div className={`grid gap-6 ${ps.length > 1 ? "sm:grid-cols-2" : ""}`}>
      {ps.map((p) => (
        <div key={`${p.a}-${p.b}`}>
          <p className="text-sm mb-2">
            {p.when && <span className="mr-2 text-xs font-semibold uppercase tracking-[0.08em] text-graphite">{p.when}</span>}
            <span className="font-semibold tabular">{messages.years(p.a, p.b)}</span>
          </p>
          <ul className="space-y-1.5">
            {p.counts.map(([pos, n]) => {
              const i = indexOf(q, pos);
              return (
                <li key={pos} className="grid grid-cols-[minmax(0,9rem)_1fr_2rem] items-center gap-3 text-sm">
                  <span className="truncate">
                    <Pos q={q} id={pos} />
                  </span>
                  <span className="h-2.5 rounded-sm bg-surface" aria-hidden="true">
                    <span
                      className="block h-full rounded-sm"
                      style={{ width: `${(n / max) * 100}%`, background: posColor(i) }}
                    />
                  </span>
                  <span className="text-right font-semibold tabular">{n}</span>
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </div>
  );
}

const RANK = { alta: 3, media: 2, baixa: 1 } as const;

/** The divergence the home page opens with: the one both the judge and the rule trust most. */
function strongest(data: Data): Divergence | undefined {
  return data.divergences
    .filter((d) => confirmed(d) && d.pair.length === 2)
    .sort(
      (a, b) =>
        RANK[b.judge?.confidence ?? "baixa"] - RANK[a.judge?.confidence ?? "baixa"] ||
        RANK[b.rule_confidence ?? "baixa"] - RANK[a.rule_confidence ?? "baixa"] ||
        b.window_end - a.window_end,
    )[0];
}

function Count({ n }: { n: number }) {
  return <span className="ml-2 font-sans text-base text-graphite tabular">{n}</span>;
}

function QuestionList({ data }: { data: Data }) {
  return (
    <ul className="border-t border-rule">
      {data.questions.map((q) => {
        const divs = data.divergences.filter((d) => d.question_id === q.id && confirmed(d));
        const rows = data.judgments.filter((j) => j.question_id === q.id);
        return (
          <li
            key={q.id}
            className="border-b border-rule py-5 grid gap-3 md:grid-cols-[1fr_16rem] md:gap-8 md:items-center"
          >
            <div>
              <Link to={`/perguntas/${q.id}`} className="font-serif text-lg leading-snug">
                {q.title}
              </Link>
              {divs.length > 0 && (
                <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-1.5">
                  {divs.map((d) => (
                    <li key={d.id}>
                      <Link to={divergenceUrl(d)} className="no-underline hover:underline">
                        <KindYears d={d} />
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div>
              <MiniStrip positions={q.positions} judgments={rows} />
              <p aria-hidden="true" className="flex justify-between text-xs text-graphite tabular mt-0.5">
                <span>{FIRST}</span>
                <span>{LAST}</span>
              </p>
              {/* the strip's key: which colour (and side) is which position */}
              <ul className="mt-1 flex flex-wrap gap-x-4 text-xs tabular">
                {q.positions.map((p, i) => (
                  <li key={p.id}>
                    <Dot index={i} />
                    {p.label} <strong className="font-semibold">{q.counts[p.id] ?? 0}</strong>
                  </li>
                ))}
              </ul>
            </div>
          </li>
        );
      })}
    </ul>
  );
}

// ---------------------------------------------------------------------------------------------
// pages

function DivergenceIndex({ data }: { data: Data }) {
  const list = data.divergences
    .filter(confirmed)
    .sort((a, b) => a.window_start - b.window_start || a.question_id.localeCompare(b.question_id));
  if (list.length === 0) return null;
  return (
    <section className={SECTION}>
      <h2 className={`${H2} mb-4`}>
        {messages.home.divergencesHeading}
        <Count n={list.length} />
      </h2>
      <ul className="border-t border-rule">
        {list.map((d) => {
          const q = data.questions.find((x) => x.id === d.question_id);
          if (!q) return null;
          return (
            <li key={d.id} className="border-b border-rule py-4 grid gap-1.5 sm:grid-cols-[10rem_1fr] sm:gap-6">
              <p>
                <KindYears d={d} />
              </p>
              <div>
                <Link to={divergenceUrl(d)} className="font-serif text-lg leading-snug">
                  {q.title}
                </Link>
                <p className="text-sm mt-0.5">
                  <Gist d={d} q={q} />
                </p>
              </div>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

export function Home({ data }: { data: Data }) {
  useTitle();
  const d = strongest(data);
  const q = d && data.questions.find((x) => x.id === d.question_id);
  const [t0, hl0, t1, hl1, t2] = messages.home.title;
  return (
    <>
      <section className={SECTION}>
        <h2 className="font-serif text-[2.25rem] sm:text-[3rem] leading-[1.1] tracking-[-0.02em] max-w-[20ch]">
          {t0}
          <span className="hl-0">{hl0}</span>
          {t1}
          <span className="hl-1">{hl1}</span>
          {t2}
        </h2>
        <p className={`mt-5 text-lg text-graphite ${MEASURE}`}>
          <strong className="font-semibold text-ink">{messages.home.leadCount(data.meta.subset_size)}</strong>
          {messages.home.leadMiddle}
          <strong className="font-semibold text-ink">{messages.home.leadQuestions(data.questions.length)}</strong>.
        </p>
        {/* search is a main way in: large, right under the claim, before anything else */}
        <div className="mt-8">
          <SearchBox size="large" />
        </div>
        <dl aria-label={messages.home.kindsLabel} className="mt-10 grid gap-2 sm:grid-cols-2 sm:gap-8 max-w-[44rem]">
          {(["shift", "split"] as const).map((k) => (
            <div key={k} className="flex items-baseline gap-3">
              <dt>
                <KindBadge type={k} />
              </dt>
              <dd className="text-sm">{messages.home.kindDef[k]}</dd>
            </div>
          ))}
        </dl>
      </section>

      {d && q && (
        <section className={SECTION} aria-labelledby="hero-q">
          <p className="text-xs font-semibold uppercase tracking-[0.08em] text-graphite">{messages.home.heroCaption}</p>
          <h3 id="hero-q" className={`${H3} mt-2 ${MEASURE}`}>
            <Link to={`/perguntas/${q.id}`}>{q.title}</Link>
          </h3>
          <p className="mt-2 mb-6 flex flex-wrap items-center gap-x-3 gap-y-1">
            <KindYears d={d} />
            <span>
              <Gist d={d} q={q} />
            </span>
          </p>
          <VoicePair items={voices(d, q)} large />
          <p className="mt-6 text-sm">
            <Link to={divergenceUrl(d)}>{messages.divergence.detail}</Link>
          </p>
        </section>
      )}

      <DivergenceIndex data={data} />

      <section className={SECTION}>
        <h2 className={`${H2} mb-4`}>
          {messages.questionsHeading}
          <Count n={data.questions.length} />
        </h2>
        {data.meta.classified === 0 && <p className="mb-3">{messages.noData}</p>}
        <QuestionList data={data} />
      </section>

      <section className={`${SECTION} grid gap-6 sm:grid-cols-2`}>
        {data.aujs.length > 0 && (
          <p>
            <Link to="/uniformizacoes" className="font-serif text-lg">
              {messages.nav.aujs}
            </Link>
            <span className={`block ${SMALL}`}>{messages.home.aujs(data.aujs.length)}</span>
          </p>
        )}
        <p>
          <Link to="/metodo" className="font-serif text-lg">
            {messages.nav.method}
          </Link>
          <span className={`block ${SMALL}`}>{messages.home.method}</span>
        </p>
      </section>
    </>
  );
}

export function Questions({ data }: { data: Data }) {
  useTitle(messages.titles.questions);
  return (
    <section>
      <h2 className={`${H2} mb-4`}>
        {messages.questionsHeading}
        <Count n={data.questions.length} />
      </h2>
      {data.meta.classified === 0 && <p className="mb-3">{messages.noData}</p>}
      <QuestionList data={data} />
    </section>
  );
}

/** Small notes under a divergence: what the reader would otherwise misread. */
function Notes({ d, aujs }: { d: Divergence; aujs: Auj[] }) {
  const dates = aujDatesIn(d, aujs);
  if (d.type !== "shift" && dates.length === 0) return null;
  return (
    <p className={`${SMALL} mt-1 ${MEASURE}`}>
      {d.type === "shift" && messages.shiftScope}
      {dates.length > 0 && `${messages.aujShort(dates)} ${messages.aujWhy}`}
    </p>
  );
}

function DivergenceCard({ d, q, aujs }: { d: Divergence; q: Question; aujs: Auj[] }) {
  return (
    <li className="py-8 border-b border-rule">
      <h4>
        <KindYears d={d} />
      </h4>
      <p className="mt-2 text-lg">
        <Gist d={d} q={q} />
      </p>
      <Notes d={d} aujs={aujs} />
      <div className="mt-5">
        <VoicePair items={voices(d, q)} />
      </div>
      <p className="mt-5 text-sm">
        <Link to={divergenceUrl(d)}>{messages.divergence.detail}</Link>
      </p>
    </li>
  );
}

function JudgmentTable({ q, rows }: { q: Question; rows: Judgment[] }) {
  return (
    <div className="overflow-x-auto -mx-4 px-4">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="text-left text-graphite">
            <th className="py-2 pr-4 font-medium">{messages.table.date}</th>
            <th className="py-2 pr-4 font-medium">{messages.table.position}</th>
            <th className="py-2 pr-4 font-medium">{messages.table.quote}</th>
            <th className="py-2 font-medium">{messages.table.link}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((j) => (
            <tr key={j.doc_id} className="align-top border-t border-rule">
              <td className="py-3 pr-4 whitespace-nowrap tabular">{fmtDate(j.date)}</td>
              <td className="py-3 pr-4 min-w-[8rem]">
                <Pos q={q} id={j.position} />
                {j.uniformizacao && <span className="block text-graphite">{messages.uniformizacao}</span>}
              </td>
              <td className="py-3 pr-4 min-w-[16rem]">
                <span className="font-serif">«{j.quote}»</span>
                <span className="block text-xs text-graphite mt-1">
                  {j.text_source === "sumario" ? messages.onlySummary : messages.fromText}
                </span>
              </td>
              <td className="py-3 whitespace-nowrap">
                <DgsiLink url={j.url}>{j.processo}</DgsiLink>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** The chart's symbols, drawn the way the chart draws them. */
function ChartLegend({ q }: { q: Question }) {
  const icon = "inline-block align-[-0.15em] mr-1.5";
  return (
    <ul aria-label={messages.timelineKey} className={`mt-2 flex flex-wrap gap-x-5 gap-y-1 ${SMALL}`}>
      {q.positions.map((p, i) => (
        <li key={p.id}>
          <Dot index={i} />
          <strong className="font-semibold" style={{ color: posColor(i) }}>
            {p.label}
          </strong>{" "}
          {i % 2 === 0 ? messages.above : messages.below}
        </li>
      ))}
      <li>
        <svg viewBox="0 0 12 12" className={`${icon} size-3`} aria-hidden="true">
          <circle cx="6" cy="6" r="3" fill="var(--graphite)" />
        </svg>
        {messages.legend.dot}
      </li>
      <li>
        <svg viewBox="0 0 12 12" className={`${icon} size-3`} aria-hidden="true">
          <circle cx="6" cy="6" r="2" fill="var(--graphite)" />
          <circle cx="6" cy="6" r="5" fill="none" stroke="var(--ink)" strokeWidth="1.25" />
        </svg>
        {messages.legend.ring}
      </li>
      <li>
        <svg viewBox="0 0 18 12" className={`${icon} h-3 w-[1.1rem]`} aria-hidden="true">
          <rect x="0.5" y="0.5" width="17" height="11" rx="2" fill="var(--surface)" stroke="var(--graphite)" strokeDasharray="2 2" />
        </svg>
        {messages.legend.band}
      </li>
    </ul>
  );
}

export function QuestionPage({ data }: { data: Data }) {
  const { id } = useParams();
  const q = data.questions.find((x) => x.id === id);
  if (!q) return <p>{messages.notFound}</p>;
  const rows = data.judgments.filter((j) => j.question_id === q.id);
  // confirmed only, as on the home page; "resolved" entries repeat the uniformização section below
  const divs = data.divergences.filter((d) => d.question_id === q.id && confirmed(d));
  const aujs = data.aujs
    .filter((a) => a.related_questions.includes(q.id))
    .sort((a, b) => a.date.localeCompare(b.date));
  return (
    <>
      <PageTitle title={q.title} />
      <section>
        <Link to="/perguntas" className="text-sm">
          {messages.back}
        </Link>
        <h2 className={`${H2} mt-6 ${MEASURE}`}>{q.title}</h2>
        <p className={`mt-3 text-lg text-graphite ${MEASURE}`}>{q.description}</p>
      </section>

      <section className="mt-8">
        <h3 className="sr-only">{messages.positionsHeading}</h3>
        <ul className="grid gap-6 grid-cols-2 max-w-[38rem]">
          {q.positions.map((p, i) => (
            <li key={p.id} className="border-t-2 pt-3" style={{ borderColor: posColor(i) }}>
              <p className="font-semibold leading-snug" style={{ color: posColor(i) }}>
                {p.label}
              </p>
              <p className="mt-1 tabular">
                <span className="font-serif text-3xl">{q.counts[p.id] ?? 0}</span>{" "}
                <span className={SMALL}>{i % 2 === 0 ? messages.above : messages.below}</span>
              </p>
            </li>
          ))}
        </ul>
        <More label={messages.definitions} className="mt-4">
          <dl className={`space-y-3 ${MEASURE}`}>
            {q.positions.map((p, i) => (
              <div key={p.id}>
                <dt className="font-semibold" style={{ color: posColor(i) }}>
                  {p.label}
                </dt>
                <dd>{p.definition}</dd>
              </div>
            ))}
          </dl>
        </More>
      </section>

      {rows.length === 0 ? (
        <p className={SECTION}>{messages.noData}</p>
      ) : (
        <>
          <section className={SECTION}>
            <h3 className={`${H3} mb-3`}>{messages.timelineHeading}</h3>
            <Timeline title={q.title} positions={q.positions} judgments={rows} divergences={divs} />
            <ChartLegend q={q} />
          </section>

          <section className={SECTION}>
            <h3 className={H3}>
              {messages.divergencesHeading}
              <Count n={divs.length} />
            </h3>
            {divs.length === 0 ? (
              <p className="mt-3">{messages.noDivergences}</p>
            ) : (
              <ul className="border-t border-rule mt-4">
                {divs.map((d) => (
                  <DivergenceCard key={d.id} d={d} q={q} aujs={aujs} />
                ))}
              </ul>
            )}
          </section>

          {aujs.length > 0 && (
            <section className={SECTION}>
              <h3 className={H3}>{messages.auj.related}</h3>
              <ul className="mt-4 space-y-8">
                {aujs.map((a) => (
                  <AujCard key={a.id} a={a} compact />
                ))}
              </ul>
            </section>
          )}

          <section className={SECTION}>
            {/* 30-180 rows: available on demand so the page reads as question, chart, divergences */}
            <More
              className="border-t border-rule pt-4"
              label={
                <>
                  {messages.tableHeading} <span className="font-normal text-graphite tabular">{rows.length}</span>
                </>
              }
            >
              <JudgmentTable q={q} rows={rows} />
            </More>
          </section>
        </>
      )}
    </>
  );
}

export function DivergencePage({ data }: { data: Data }) {
  const { id } = useParams();
  const d = data.divergences.find((x) => x.id === id);
  const q = d && data.questions.find((x) => x.id === d.question_id);
  if (!d || !q) return <p>{messages.divergence.notFound}</p>;
  const aujs = data.aujs.filter((a) => a.related_questions.includes(q.id));
  const t = messages.divergence;
  return (
    <>
      <PageTitle title={`${messages.kind[d.type]} ${messages.years(d.window_start, d.window_end)}: ${q.title}`} />
      <section>
        <Link to={`/perguntas/${q.id}`} className="text-sm">
          {q.title}
        </Link>
        <p className="mt-6">
          <KindYears d={d} />
        </p>
        <h2 className={`${H2} mt-2 ${MEASURE}`}>
          <Gist d={d} q={q} />
        </h2>
        <Notes d={d} aujs={aujs} />
        {d.type === "shift" && (
          <p className="text-sm mt-1">
            <Link to={`/perguntas/${q.id}`}>{t.toChart}</Link>
          </p>
        )}
        <div className="mt-8">
          <VoicePair items={voices(d, q)} large />
        </div>
      </section>

      <section className={`${SECTION} max-w-[44rem]`}>
        <h3 className={`${H3} mb-4`}>{t.evidence}</h3>
        <Evidence d={d} q={q} judgments={data.judgments} />
      </section>

      <section className={`mt-10 ${MEASURE}`}>
        <More label={t.how} className="border-t border-rule pt-4">
          <p>{t.rule[d.type]}</p>
          {d.judge && (
            <>
              <p>{t.judge}</p>
              <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-sm">
                <dt className="text-graphite">{t.judgeConfidence}</dt>
                <dd className="font-semibold">{t.level[d.judge.confidence]}</dd>
                {d.rule_confidence && (
                  <>
                    <dt className="text-graphite">{t.ruleConfidence}</dt>
                    <dd className="font-semibold">{t.level[d.rule_confidence]}</dd>
                  </>
                )}
              </dl>
              <p className={SMALL}>{t.ruleConfidenceNote}</p>
              <div>
                <p className={SMALL}>{t.rationale}</p>
                <p className="font-serif mt-1">{d.judge.rationale}</p>
              </div>
            </>
          )}
          {d.display === "possivel_alteracao_legislativa" && <p>{messages.legislative}</p>}
        </More>
      </section>
    </>
  );
}

/**
 * One uniformização. On its own page it opens with what it is about and the ruling; on a question
 * page (`compact`) the question is already known, so the ruling waits behind a click too.
 */
export function AujCard({ a, questions = [], compact = false }: { a: Auj; questions?: Question[]; compact?: boolean }) {
  const about = questions.filter((q) => a.related_questions.includes(q.id));
  const ruling = (
    <div className={`bg-surface border-l-2 border-ink px-5 py-4 ${MEASURE}`}>
      <p className="text-xs font-semibold uppercase tracking-[0.08em] text-graphite">{messages.auj.ruling}</p>
      <p className="voice mt-1">«{a.ruling_quote}»</p>
    </div>
  );
  return (
    <li className="border-t border-ink pt-5">
      <h3>
        <strong className="font-semibold tabular">{fmtDate(a.date)}</strong>{" "}
        <span className={`${SMALL} tabular`}>{messages.auj.processo(a.processo)}</span>
      </h3>
      {about.length > 0 && (
        <p className="mt-2 font-serif text-lg leading-snug">
          <span className={`${SMALL} font-sans mr-2`}>{messages.auj.about}</span>
          {about.map((q, i) => (
            <span key={q.id}>
              {i > 0 && "; "}
              <Link to={`/perguntas/${q.id}`}>{q.title}</Link>
            </span>
          ))}
        </p>
      )}
      {compact ? (
        <More label={messages.auj.showRuling} className="mt-3">
          {ruling}
        </More>
      ) : (
        <div className="mt-4">{ruling}</div>
      )}
      <More label={messages.auj.more} className="mt-4">
        {a.question_quote && (
          <div className={MEASURE}>
            <p className={SMALL}>{messages.auj.question}</p>
            <p className="voice mt-1">«{a.question_quote}»</p>
          </div>
        )}
        <div className={MEASURE}>
          <p className={SMALL}>{messages.auj.conflict}</p>
          <p className="voice mt-1">«{a.conflict_quote}»</p>
        </div>
        <div className="pt-3 grid gap-8 sm:grid-cols-2 sm:gap-10">
          {a.sides.map((s, i) => (
            <section
              key={s.auj_quote}
              aria-label={messages.auj.side(i + 1)}
              className="border-t border-rule pt-3 space-y-3"
            >
              <p className="text-sm font-semibold">{messages.auj.side(i + 1)}</p>
              <p className="voice">«{s.auj_quote}»</p>
              {s.judgments.length === 0 ? (
                <p className={SMALL}>{messages.auj.noneNamed}</p>
              ) : (
                <>
                  <p className={SMALL}>{messages.auj.named}</p>
                  <ul className="space-y-4">
                    {s.judgments.map((j) => (
                      <li key={j.doc_id}>
                        <p className="font-serif">«{j.quote}»</p>
                        <p className={`${SMALL} mt-1`}>
                          {fmtDate(j.date)}, <DgsiLink url={j.url}>{j.processo}</DgsiLink>
                        </p>
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </section>
          ))}
        </div>
      </More>
      <p className="mt-3 text-sm">
        <DgsiLink url={a.url}>{messages.auj.open}</DgsiLink>
      </p>
    </li>
  );
}

export function AujPage({ data }: { data: Data }) {
  useTitle(messages.titles.aujs);
  return (
    <section>
      <h2 className={H2}>
        {messages.auj.heading}
        <Count n={data.aujs.length} />
      </h2>
      <p className={`mt-3 text-lg text-graphite ${MEASURE}`}>{messages.auj.intro}</p>
      <ul className="mt-10 space-y-14">
        {data.aujs.map((a) => (
          <AujCard key={a.id} a={a} questions={data.questions} />
        ))}
      </ul>
    </section>
  );
}

const ratio = ([n, d]: [number, number]) => (d ? `${n}/${d} (${Math.round((100 * n) / d)} %)` : "—");

function ScoreTable({ rows }: { rows: Score[] }) {
  const m = messages.method_page;
  return (
    <div className="overflow-x-auto -mx-4 px-4">
      <table className="w-full text-sm border-collapse tabular">
        <thead>
          <tr className="text-left text-graphite">
            <th className="py-2 pr-4 font-medium">{m.cols.set}</th>
            <th className="py-2 pr-4 font-medium">{m.cols.system}</th>
            <th className="py-2 pr-4 font-medium">{m.cols.exact}</th>
            <th className="py-2 pr-4 font-medium">{m.cols.recall}</th>
            <th className="py-2 font-medium">{m.cols.precision}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={`${r.set}-${r.system}`} className="border-t border-rule">
              <td className="py-2 pr-4 whitespace-nowrap">
                {m.set[r.set]} ({r.rows})
              </td>
              <td className={`py-2 pr-4 ${r.system === "model" ? "font-semibold" : ""}`}>{m.system[r.system]}</td>
              <td className="py-2 pr-4 whitespace-nowrap">{ratio(r.exact)}</td>
              <td className="py-2 pr-4 whitespace-nowrap">{ratio(r.recall)}</td>
              <td className="py-2 whitespace-nowrap">{ratio(r.precision)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** A number that matters, big; what it is, small; the caveat, smaller. */
function Stat({ value, title, sub }: { value: ReactNode; title: string; sub?: string }) {
  return (
    <li className="border-t border-rule pt-3">
      <p className="font-serif text-[2rem] leading-none tabular">{value}</p>
      <p className="mt-1.5 text-sm font-semibold">{title}</p>
      {sub && <p className={`${SMALL} mt-1`}>{sub}</p>}
    </li>
  );
}

export function MethodPage({ data }: { data: Data }) {
  useTitle(messages.titles.method);
  const m = messages.method_page;
  const s = m.stats;
  const ev = data.evaluation;
  const labels = ev?.divergence_labels;
  const shown = labels?.shown ?? {};
  const decided = (shown.correct ?? 0) + (shown.incorrect ?? 0) + (shown.legislative_change ?? 0);
  const labelled = decided + (shown.unclear ?? 0);
  return (
    <>
      <section>
        <h2 className={H2}>{m.heading}</h2>
      </section>

      <section className="mt-8">
        <h3 className="sr-only">{m.numbersHeading}</h3>
        {ev === null ? (
          <p>{m.unavailable}</p>
        ) : (
          <ul className="grid gap-x-8 gap-y-6 sm:grid-cols-2 lg:grid-cols-3">
            <Stat value={ev.grounding.accepted} title={s.quotes} sub={s.quotesSub(ev.grounding.rejected)} />
            <Stat
              value={ev.divergences.shown_v2}
              title={s.divergences}
              sub={s.divergencesSub(ev.divergences.judged)}
            />
            {labels && labelled > 0 ? (
              <Stat
                value={s.labels(shown.correct ?? 0, decided)}
                title={s.labelsTitle}
                sub={s.labelsSub(
                  labelled,
                  shown.correct ?? 0,
                  decided - (shown.correct ?? 0),
                  shown.unclear ?? 0,
                  labels.labellers.join("; "),
                )}
              />
            ) : (
              <li className={`border-t border-rule pt-3 ${SMALL}`}>{s.noLabels}</li>
            )}
            <Stat value={ev.aujs} title={s.aujs} />
            <Stat
              value={s.cost(ev.cost.usd_estimate.toLocaleString("pt-PT"))}
              title={s.costTitle}
              sub={s.costSub((ev.cost.input_tokens + ev.cost.output_tokens).toLocaleString("pt-PT"))}
            />
          </ul>
        )}
      </section>

      <section className={`${SECTION} ${MEASURE}`}>
        <h3 className={H3}>{m.stepsHeading}</h3>
        <ol className="mt-4 space-y-3">
          {m.steps.map(([head, rest]) => (
            <li key={head}>
              <strong className="font-semibold">{head}</strong>
              {rest}
            </li>
          ))}
        </ol>
      </section>

      <section className={`${SECTION} space-y-2 border-t border-rule pt-4`}>
        {ev !== null && (
          <>
            <More label={m.accuracyHeading}>
              <p className={`${SMALL} ${MEASURE}`}>{m.accuracyNote}</p>
              <ScoreTable rows={ev.position} />
              <p className={`${SMALL} ${MEASURE}`}>{s.pairRule(ev.divergences.shown_v1, ev.divergences.shown_v2)}</p>
            </More>
            <More label={m.surveyHeading}>
              <ul className={`space-y-2 ${MEASURE}`}>
                {ev.survey.map((x) => (
                  <li key={x.seed}>
                    {x.topic}: <strong className="font-semibold">{x.result}</strong>
                  </li>
                ))}
              </ul>
            </More>
          </>
        )}
        <More label={m.limitsHeading}>
          <ul className={`space-y-2 list-disc pl-6 marker:text-graphite ${MEASURE}`}>
            {m.limits.map((l) => (
              <li key={l}>{l}</li>
            ))}
          </ul>
        </More>
        <p className="pt-4">
          <a href={m.reportUrl} rel="noopener noreferrer" target="_blank">
            {m.report}
          </a>
        </p>
      </section>
    </>
  );
}
