import { Link, useParams } from "react-router-dom";
import type { Data, Divergence, Judgment, Question } from "./data";
import { messages } from "./messages.pt";
import { Marker, Timeline } from "./Timeline";

export function Home({ data }: { data: Data }) {
  return (
    <section className="space-y-3">
      <p>{messages.summary(data.meta.subset_size, data.meta.classified)}</p>
      <p className="text-[color:var(--color-muted)]">{messages.method}</p>
      <p>
        <Link to="/perguntas" className="underline text-[color:var(--color-accent)]">
          {messages.nav.questions}
        </Link>
      </p>
    </section>
  );
}

function countOf(q: Question): number {
  return Object.values(q.counts).reduce((a, b) => a + b, 0);
}

export function Questions({ data }: { data: Data }) {
  return (
    <section>
      <h2 className="text-xl font-semibold mb-3">{messages.questionsHeading}</h2>
      {data.meta.classified === 0 && <p className="mb-3">{messages.noData}</p>}
      <ul className="space-y-3">
        {data.questions.map((q) => {
          const divs = data.divergences.filter((d) => d.question_id === q.id);
          return (
            <li key={q.id} className="rounded border border-[color:var(--color-rule)] p-3">
              <Link
                to={`/perguntas/${q.id}`}
                className="font-medium underline text-[color:var(--color-accent)]"
              >
                {q.title}
              </Link>
              <p className="text-sm text-[color:var(--color-muted)]">
                {messages.judgmentsCount(countOf(q))}
                {q.first_year !== null && q.last_year !== null &&
                  ` · ${messages.years(q.first_year, q.last_year)}`}
                {divs.length > 0 && ` · ${messages.divergencesCount(divs.length)}`}
              </p>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

function DivergenceCard({ d, q }: { d: Divergence; q: Question }) {
  const label = (id: string) => q.positions.find((p) => p.id === id)?.label ?? id;
  return (
    <li className="rounded border border-[color:var(--color-rule)] p-3 space-y-2">
      <p className="font-medium">
        {messages.display[d.display]} · {messages.type[d.type]} ·{" "}
        {messages.years(d.window_start, d.window_end)}
        {d.rule_confidence && (
          <span className="text-sm text-[color:var(--color-muted)]">
            {" "}
            ({messages.confidence[d.rule_confidence]})
          </span>
        )}
      </p>
      {d.pair.map((p) => (
        <blockquote key={p.doc_id} className="border-l-4 border-[color:var(--color-rule)] pl-3">
          <p className="text-sm text-[color:var(--color-muted)]">
            {p.date} · {label(p.position)} ·{" "}
            <a href={p.url} rel="noopener noreferrer" target="_blank" className="underline">
              {p.processo || messages.table.open}
            </a>
          </p>
          <p>«{p.quote}»</p>
        </blockquote>
      ))}
    </li>
  );
}

function JudgmentTable({ q, rows }: { q: Question; rows: Judgment[] }) {
  const index = (id: string) => q.positions.findIndex((p) => p.id === id);
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left">
            <th className="p-1">{messages.table.date}</th>
            <th className="p-1">{messages.table.position}</th>
            <th className="p-1">{messages.table.quote}</th>
            <th className="p-1">{messages.table.link}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((j) => (
            <tr key={j.doc_id} className="align-top border-t border-[color:var(--color-rule)]">
              <td className="p-1 whitespace-nowrap">{j.date}</td>
              <td className="p-1">
                <svg width="14" height="14" aria-hidden="true" className="inline mr-1">
                  <Marker index={index(j.position)} x={7} y={7} />
                </svg>
                {q.positions[index(j.position)]?.label ?? j.position}
                {j.uniformizacao && ` (${messages.uniformizacao})`}
              </td>
              <td className="p-1">
                «{j.quote}»
                <span className="block text-xs text-[color:var(--color-muted)]">
                  {j.text_source === "sumario" ? messages.onlySummary : messages.fromText}
                </span>
              </td>
              <td className="p-1">
                <a href={j.url} rel="noopener noreferrer" target="_blank" className="underline">
                  {j.processo}
                </a>
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
  return (
    <section className="space-y-4">
      <Link to="/perguntas" className="underline text-[color:var(--color-accent)]">
        {messages.back}
      </Link>
      <h2 className="text-xl font-semibold">{q.title}</h2>
      <p>{q.description}</p>
      <p className="text-sm text-[color:var(--color-muted)]">{messages.splitTag[q.split]}</p>
      <h3 className="font-semibold">{messages.positionsHeading}</h3>
      <ul className="space-y-1">
        {q.positions.map((p, i) => (
          <li key={p.id}>
            <svg width="14" height="14" aria-hidden="true" className="inline mr-1">
              <Marker index={i} x={7} y={7} />
            </svg>
            <strong>{p.label}</strong> ({q.counts[p.id] ?? 0}): {p.definition}
          </li>
        ))}
      </ul>
      {rows.length === 0 ? (
        <p>{messages.noData}</p>
      ) : (
        <>
          <h3 className="font-semibold">{messages.timelineHeading}</h3>
          <Timeline title={q.title} positions={q.positions} judgments={rows} divergences={divs} />
          <h3 className="font-semibold">{messages.divergencesHeading}</h3>
          {divs.length === 0 ? (
            <p>{messages.noDivergences}</p>
          ) : (
            <ul className="space-y-3">
              {divs.map((d) => (
                <DivergenceCard key={d.id} d={d} q={q} />
              ))}
            </ul>
          )}
          <h3 className="font-semibold">{messages.tableHeading}</h3>
          <JudgmentTable q={q} rows={rows} />
        </>
      )}
    </section>
  );
}
