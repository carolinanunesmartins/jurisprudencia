import type { ReactNode } from "react";
import { Link, useParams } from "react-router-dom";
import type { Auj, Data, Divergence, Judgment, Question, Score } from "./data";
import { messages } from "./messages.pt";
import { MiniStrip, posColor, Timeline } from "./Timeline";

// ---------------------------------------------------------------------------------------------
// shared pieces

/** "2019-10-29" -> "29 out. 2019" (browsers format pt-PT short dates as 29/10/2019). */
export function fmtDate(iso: string): string {
  const [y, m, d] = iso.split("-").map(Number);
  const month = m ? messages.months[m - 1] : undefined;
  return y && month && d ? `${d} ${month} ${y}` : iso;
}

function DgsiLink({ url, children }: { url: string; children: ReactNode }) {
  return (
    <a href={url} rel="noopener noreferrer" target="_blank" className="tabular">
      {children}
    </a>
  );
}

const SECTION = "mt-14 first:mt-0";
const H2 = "font-serif text-[1.75rem] leading-tight tracking-[-0.01em]";
const H3 = "font-serif text-xl leading-snug";
const SMALL = "text-sm text-graphite";
const MEASURE = "max-w-[38rem]";

function Dot({ index }: { index: number }) {
  return (
    <span
      aria-hidden="true"
      className="inline-block size-2.5 rounded-full align-[0.05em] mr-2"
      style={{ background: posColor(index) }}
    />
  );
}

type VoiceItem = {
  doc_id: string;
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
    <article className="border-t-2 pt-3 flex flex-col gap-3" style={{ borderColor: colour ?? "var(--rule)" }}>
      <p className="text-sm font-semibold" style={{ color: colour }}>
        {v.label}
      </p>
      <blockquote className={`voice ${large ? "text-[1.3rem] leading-[1.5]" : ""}`}>«{v.quote}»</blockquote>
      <p className={SMALL}>
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
  return d.pair.map((p) => {
    const index = q.positions.findIndex((x) => x.id === p.position);
    return {
      doc_id: p.doc_id,
      index,
      label: q.positions[index]?.label ?? p.position,
      date: p.date,
      processo: p.processo,
      url: p.url,
      quote: p.quote,
    };
  });
}

const RANK = { alta: 3, media: 2, baixa: 1 } as const;

/** The divergence the home page opens with: the one both the judge and the rule trust most. */
function strongest(data: Data): Divergence | undefined {
  return data.divergences
    .filter((d) => d.type !== "resolved" && d.judge?.real_opposition && d.pair.length === 2)
    .sort(
      (a, b) =>
        RANK[b.judge?.confidence ?? "baixa"] - RANK[a.judge?.confidence ?? "baixa"] ||
        RANK[b.rule_confidence ?? "baixa"] - RANK[a.rule_confidence ?? "baixa"] ||
        b.window_end - a.window_end,
    )[0];
}

function countOf(q: Question): number {
  return Object.values(q.counts).reduce((a, b) => a + b, 0);
}

function QuestionList({ data }: { data: Data }) {
  return (
    <ul className="border-t border-rule">
      {data.questions.map((q) => {
        const divs = data.divergences.filter((d) => d.question_id === q.id && d.type !== "resolved");
        const rows = data.judgments.filter((j) => j.question_id === q.id);
        const meta = [
          messages.judgmentsCount(countOf(q)),
          q.first_year !== null && q.last_year !== null ? messages.years(q.first_year, q.last_year) : null,
          divs.length > 0 ? messages.divergencesCount(divs.length) : null,
        ].filter(Boolean);
        return (
          <li
            key={q.id}
            className="border-b border-rule py-5 grid gap-3 md:grid-cols-[1fr_16rem] md:gap-8 md:items-center"
          >
            <div>
              <Link to={`/perguntas/${q.id}`} className="font-serif text-lg leading-snug">
                {q.title}
              </Link>
              <p className={`${SMALL} tabular mt-1`}>{meta.join(", ")}</p>
            </div>
            <MiniStrip positions={q.positions} judgments={rows} />
          </li>
        );
      })}
    </ul>
  );
}

// ---------------------------------------------------------------------------------------------
// pages

export function Home({ data }: { data: Data }) {
  const d = strongest(data);
  const q = d && data.questions.find((x) => x.id === d.question_id);
  return (
    <>
      <section className={SECTION}>
        <h2 className="font-serif text-[2.25rem] sm:text-[3rem] leading-[1.08] tracking-[-0.02em] max-w-[22ch]">
          {messages.tagline}
        </h2>
        <p className={`mt-5 text-lg text-graphite ${MEASURE}`}>{messages.home.lead(data.meta.subset_size)}</p>
      </section>

      {d && q && (
        <section className={SECTION} aria-labelledby="hero-q">
          <p className={SMALL}>{messages.home.heroCaption}</p>
          <h3 id="hero-q" className={`${H3} mt-1 mb-6 ${MEASURE}`}>
            <Link to={`/perguntas/${q.id}`}>{q.title}</Link>
          </h3>
          <VoicePair items={voices(d, q)} large />
          <p className="mt-6">
            <Link to={`/divergencias/${encodeURIComponent(d.id)}`}>{messages.home.openHero}</Link>
          </p>
        </section>
      )}

      <section className={SECTION}>
        <h2 className={H2}>{messages.questionsHeading}</h2>
        <p className={`${SMALL} mt-2 mb-4 ${MEASURE}`}>{messages.home.questionsIntro}</p>
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
  return (
    <section>
      <h2 className={H2}>{messages.questionsHeading}</h2>
      <p className={`${SMALL} mt-2 mb-4 ${MEASURE}`}>{messages.home.questionsIntro}</p>
      {data.meta.classified === 0 && <p className="mb-3">{messages.noData}</p>}
      <QuestionList data={data} />
    </section>
  );
}

function DivergenceCard({ d, q }: { d: Divergence; q: Question }) {
  return (
    <li className="py-8 border-b border-rule">
      <h4 className="font-semibold">{messages.kind[d.type]}</h4>
      <p className={`${SMALL} tabular mb-5`}>
        {messages.years(d.window_start, d.window_end)}
        {d.rule_confidence && <>, {messages.confidence[d.rule_confidence]}</>}
        {d.display === "possivel_alteracao_legislativa" && <>. {messages.legislative}</>}
      </p>
      <VoicePair items={voices(d, q)} />
      <p className="mt-5 text-sm">
        <Link to={`/divergencias/${encodeURIComponent(d.id)}`}>{messages.divergence.detail}</Link>
      </p>
    </li>
  );
}

function JudgmentTable({ q, rows }: { q: Question; rows: Judgment[] }) {
  const index = (id: string) => q.positions.findIndex((p) => p.id === id);
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
                <Dot index={index(j.position)} />
                {q.positions[index(j.position)]?.label ?? j.position}
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

export function QuestionPage({ data }: { data: Data }) {
  const { id } = useParams();
  const q = data.questions.find((x) => x.id === id);
  if (!q) return <p>{messages.notFound}</p>;
  const rows = data.judgments.filter((j) => j.question_id === q.id);
  const divs = data.divergences.filter((d) => d.question_id === q.id);
  const aujs = data.aujs.filter((a) => a.related_questions.includes(q.id));
  return (
    <>
      <section>
        <Link to="/perguntas" className="text-sm">
          {messages.back}
        </Link>
        <p className={`${SMALL} mt-6`}>{messages.splitTag[q.split]}</p>
        <h2 className={`${H2} mt-1 ${MEASURE}`}>{q.title}</h2>
        <p className={`mt-3 text-lg text-graphite ${MEASURE}`}>{q.description}</p>
      </section>

      <section className={SECTION}>
        <h3 className="sr-only">{messages.positionsHeading}</h3>
        <ul className="grid gap-6 sm:grid-cols-2">
          {q.positions.map((p, i) => (
            <li key={p.id} className="border-t-2 pt-3" style={{ borderColor: posColor(i) }}>
              <p className="font-semibold" style={{ color: posColor(i) }}>
                {p.label}
              </p>
              <p className={`${SMALL} tabular`}>
                {messages.judgmentsCount(q.counts[p.id] ?? 0)}, {i % 2 === 0 ? messages.above : messages.below}
              </p>
              <p className="mt-2">{p.definition}</p>
            </li>
          ))}
        </ul>
      </section>

      {rows.length === 0 ? (
        <p className={SECTION}>{messages.noData}</p>
      ) : (
        <>
          <section className={SECTION}>
            <h3 className={H3}>{messages.timelineHeading}</h3>
            <div className="mt-4">
              <Timeline title={q.title} positions={q.positions} judgments={rows} divergences={divs} />
            </div>
            <p className={`${SMALL} mt-2 ${MEASURE}`}>{messages.timelineNote}</p>
          </section>

          <section className={SECTION}>
            <h3 className={H3}>{messages.divergencesHeading}</h3>
            {divs.length === 0 ? (
              <p className="mt-3">{messages.noDivergences}</p>
            ) : (
              <ul className="border-t border-rule mt-4">
                {divs.map((d) => (
                  <DivergenceCard key={d.id} d={d} q={q} />
                ))}
              </ul>
            )}
          </section>

          {aujs.length > 0 && (
            <section className={SECTION}>
              <h3 className={H3}>{messages.auj.related}</h3>
              <ul className="mt-4 space-y-10">
                {aujs.map((a) => (
                  <AujCard key={a.id} a={a} />
                ))}
              </ul>
            </section>
          )}

          <section className={SECTION}>
            {/* 30-180 rows: available on demand so the page reads as question, chart, divergences */}
            <details className="group border-t border-rule pt-4">
              <summary className={`${H3} cursor-pointer list-none flex items-baseline gap-3`}>
                <span
                  aria-hidden="true"
                  className="inline-block text-graphite transition-transform duration-200 group-open:rotate-90"
                >
                  ›
                </span>
                {messages.tableHeading}
                <span className={`${SMALL} font-sans tabular`}>{rows.length}</span>
              </summary>
              <div className="mt-4">
                <JudgmentTable q={q} rows={rows} />
              </div>
            </details>
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
  const label = (pos: string) => q.positions.find((p) => p.id === pos)?.label ?? pos;
  return (
    <>
      <section>
        <Link to={`/perguntas/${q.id}`} className="text-sm">
          {messages.divergence.backTo(q.title)}
        </Link>
        <h2 className={`${H2} mt-6`}>{messages.kind[d.type]}</h2>
        <p className={`${SMALL} tabular mt-1 mb-8`}>
          {messages.years(d.window_start, d.window_end)}
          {d.rule_confidence && <>, {messages.confidence[d.rule_confidence]}</>}
          {d.display === "possivel_alteracao_legislativa" && <>. {messages.legislative}</>}
        </p>
        <VoicePair items={voices(d, q)} large />
      </section>

      <section className={`${SECTION} ${MEASURE}`}>
        <h3 className={H3}>{messages.divergence.how}</h3>
        <ul className="mt-4 space-y-4 border-l border-rule pl-5">
          <li>{messages.divergence.window(d.window_start, d.window_end)}</li>
          <li className="tabular">
            {messages.divergence.support}{" "}
            {Object.entries(d.support)
              .map(([pos, n]) => `${label(pos)}, ${n}`)
              .join("; ")}
          </li>
          <li>{messages.divergence.rule[d.type]}</li>
          {d.judge && (
            <li>
              {messages.divergence.judge(messages.divergence.judgeConfidence[d.judge.confidence])}
              <p className={`${SMALL} mt-3`}>{messages.divergence.rationale}</p>
              <p className="font-serif mt-1">{d.judge.rationale}</p>
            </li>
          )}
          {d.rule_confidence && (
            <li>
              <span className="font-semibold">{messages.confidenceTitle[d.rule_confidence]}</span>{" "}
              {messages.divergence.ruleConfidence}
            </li>
          )}
        </ul>
      </section>
    </>
  );
}

export function AujCard({ a }: { a: Auj }) {
  return (
    <li className="border-t border-ink pt-5">
      <h3 className="font-semibold">{messages.auj.title(fmtDate(a.date), a.processo)}</h3>
      {a.question_quote && (
        <div className={`mt-5 ${MEASURE}`}>
          <p className={SMALL}>{messages.auj.question}</p>
          <p className="voice mt-1">«{a.question_quote}»</p>
        </div>
      )}
      <div className={`mt-5 ${MEASURE}`}>
        <p className={SMALL}>{messages.auj.conflict}</p>
        <p className="voice mt-1">«{a.conflict_quote}»</p>
      </div>
      <div className="mt-8 grid gap-8 sm:grid-cols-2 sm:gap-10">
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
      <div className="mt-8 bg-surface border-l-2 border-ink px-5 py-4">
        <p className="text-sm font-semibold">{messages.auj.ruling}</p>
        <p className="voice mt-1">«{a.ruling_quote}»</p>
      </div>
      <p className="mt-4 text-sm">
        <DgsiLink url={a.url}>{messages.auj.open}</DgsiLink>
      </p>
    </li>
  );
}

export function AujPage({ data }: { data: Data }) {
  return (
    <section>
      <h2 className={H2}>{messages.auj.heading}</h2>
      <p className={`mt-3 text-lg text-graphite ${MEASURE}`}>{messages.auj.intro}</p>
      <ul className="mt-10 space-y-16">
        {data.aujs.map((a) => (
          <AujCard key={a.id} a={a} />
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

export function MethodPage({ data }: { data: Data }) {
  const m = messages.method_page;
  const ev = data.evaluation;
  const labels = ev?.divergence_labels;
  const shown = labels?.shown ?? {};
  const decided = (shown.correct ?? 0) + (shown.incorrect ?? 0) + (shown.legislative_change ?? 0);
  const labelled = decided + (shown.unclear ?? 0);
  return (
    <>
      <section className={MEASURE}>
        <h2 className={H2}>{m.heading}</h2>
        <h3 className={`${H3} mt-10`}>{m.stepsHeading}</h3>
        <ol className="mt-4 space-y-4 list-decimal pl-6 marker:text-graphite">
          {m.steps.map((s) => (
            <li key={s} className="pl-1">
              {s}
            </li>
          ))}
        </ol>
      </section>

      <section className={SECTION}>
        <h3 className={H3}>{m.numbersHeading}</h3>
        {ev === null ? (
          <p className="mt-3">{m.unavailable}</p>
        ) : (
          <>
            <ul className={`mt-4 space-y-3 ${MEASURE}`}>
              <li>{m.grounding(ev.grounding.proposed, ev.grounding.accepted, ev.grounding.rejected)}</li>
              <li>
                {m.divergences(
                  ev.divergences.judged,
                  ev.divergences.shown_v1,
                  ev.divergences.shown_v2,
                  ev.divergences.shown_v2_test,
                )}
              </li>
              <li>
                {labels && labelled > 0
                  ? m.labels(shown.correct ?? 0, decided, shown.unclear ?? 0, labels.labellers.join("; "))
                  : m.noLabels}
              </li>
              <li>{m.aujs(ev.aujs)}</li>
              <li>
                {m.cost(
                  (ev.cost.input_tokens + ev.cost.output_tokens).toLocaleString("pt-PT"),
                  ev.cost.usd_estimate.toLocaleString("pt-PT"),
                )}
              </li>
            </ul>
            <h4 className="font-semibold mt-10">{m.accuracyHeading}</h4>
            <p className={`${SMALL} mt-1 mb-3 ${MEASURE}`}>{m.accuracyNote}</p>
            <ScoreTable rows={ev.position} />
            <h4 className="font-semibold mt-10">{m.surveyHeading}</h4>
            <ul className={`mt-3 space-y-2 ${MEASURE}`}>
              {ev.survey.map((s) => (
                <li key={s.seed}>
                  {s.topic}: <span className="font-semibold">{s.result}</span>
                </li>
              ))}
            </ul>
          </>
        )}
      </section>

      <section className={`${SECTION} ${MEASURE}`}>
        <h3 className={H3}>{m.limitsHeading}</h3>
        <ul className="mt-4 space-y-3 list-disc pl-6 marker:text-graphite">
          {m.limits.map((l) => (
            <li key={l}>{l}</li>
          ))}
        </ul>
        <p className="mt-8">
          <a href={m.reportUrl} rel="noopener noreferrer" target="_blank">
            {m.report}
          </a>
        </p>
      </section>
    </>
  );
}
