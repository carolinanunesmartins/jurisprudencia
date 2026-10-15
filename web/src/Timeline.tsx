import type { Divergence, Judgment, Position } from "./data";
import { messages } from "./messages.pt";

export const FIRST = 2000;
export const LAST = 2025;
const YEARS = LAST - FIRST + 1;
const W = 720;
const PAD = 8;
const COL = (W - 2 * PAD) / YEARS;
const PER_ROW = 3; // dots side by side in one year column
const STEP = 7.5;
const R = 3;

export const posColor = (index: number) => `var(--pos-${index % 4})`;

// Side of the axis per position: the first position above, the second below. Questions have two
// positions (SPEC §5.1 allows up to four); extra ones share the sides in turn.
const sideOf = (index: number) => (index % 2 === 0 ? -1 : 1);

type Column = { key: string; lane: number; year: number; js: Judgment[] };

/** Judgments grouped by (position, year). */
function columns(judgments: Judgment[], positions: Position[]): Column[] {
  const cols = new Map<string, Column>();
  for (const j of judgments) {
    const lane = positions.findIndex((p) => p.id === j.position);
    if (lane < 0) continue;
    const year = Number(j.date.slice(0, 4));
    const key = `${lane}:${year}`;
    const col = cols.get(key) ?? { key, lane, year, js: [] };
    col.js.push(j);
    cols.set(key, col);
  }
  return [...cols.values()];
}

const xOfYear = (year: number) => PAD + (year - FIRST) * COL + COL / 2;

type Props = {
  title: string;
  positions: Position[];
  judgments: Judgment[];
  divergences: Divergence[];
};

/** Mirrored year histogram: each judgment is a dot; one position above the axis, one below. */
export function Timeline({ title, positions, judgments, divergences }: Props) {
  const cols = columns(judgments, positions);
  const rows = Math.max(1, ...cols.map((c) => Math.ceil(c.js.length / PER_ROW)));
  const half = rows * STEP + 10;
  const axis = half;
  const height = 2 * half + 4;
  return (
    <div>
      <svg viewBox={`0 0 ${W} ${height}`} role="img" aria-label={messages.timelineLabel(title)} className="block w-full h-auto">
        {divergences
          .filter((d) => d.type !== "resolved")
          .map((d) => (
            // a dashed outline as well as the fill: the fill alone is too faint to see on paper
            <rect
              key={d.id}
              x={xOfYear(d.window_start) - COL / 2}
              y={2}
              width={(d.window_end - d.window_start + 1) * COL}
              height={2 * half - 4}
              fill="var(--surface)"
              stroke="var(--graphite)"
              strokeWidth={1}
              strokeDasharray="3 3"
              rx={3}
            />
          ))}
        <line x1={PAD} x2={W - PAD} y1={axis} y2={axis} stroke="var(--ink)" strokeWidth={1} />
        {cols.map(({ lane, year, js }) => {
          const side = sideOf(lane);
          return js.map((j, n) => {
            const cx = xOfYear(year) + ((n % PER_ROW) - 1) * STEP;
            const cy = axis + side * (8 + Math.floor(n / PER_ROW) * STEP);
            return (
              <g key={`${j.doc_id}-${j.question_id}`}>
                <title>{`${j.processo}, ${j.date}`}</title>
                <circle cx={cx} cy={cy} r={R} fill={posColor(lane)} />
                {j.uniformizacao && (
                  <circle cx={cx} cy={cy} r={R + 3} fill="none" stroke="var(--ink)" strokeWidth={1.25} />
                )}
              </g>
            );
          });
        })}
        {TICKS.map((t) => (
          <line key={t} x1={xOfYear(t)} x2={xOfYear(t)} y1={axis - 3} y2={axis + 3} stroke="var(--ink)" />
        ))}
      </svg>
      <YearAxis />
    </div>
  );
}

const TICKS = [2000, 2005, 2010, 2015, 2020, 2025];

/** Year labels in HTML, not in the SVG: they keep their size when the chart shrinks on a phone. */
function YearAxis() {
  return (
    <div aria-hidden="true" className="relative h-5 mt-1 text-xs text-graphite tabular">
      {TICKS.map((t) => (
        <span key={t} className="absolute -translate-x-1/2" style={{ left: `${(xOfYear(t) / W) * 100}%` }}>
          {t}
        </span>
      ))}
    </div>
  );
}

/** The same picture at thumbnail size for the question list: bars instead of dots. */
export function MiniStrip({ positions, judgments }: { positions: Position[]; judgments: Judgment[] }) {
  const cols = columns(judgments, positions);
  const max = Math.max(1, ...cols.map((c) => c.js.length));
  const H = 22;
  return (
    <svg viewBox={`0 0 ${W} ${2 * H + 2}`} aria-hidden="true" className="block w-full h-12" preserveAspectRatio="none">
      <line x1={PAD} x2={W - PAD} y1={H + 1} y2={H + 1} stroke="var(--rule)" />
      {cols.map(({ key, lane, year, js }) => {
        // square root: one busy year should not flatten all the others
        const h = Math.max(3, Math.sqrt(js.length / max) * H);
        const side = sideOf(lane);
        return (
          <rect
            key={key}
            x={xOfYear(year) - COL * 0.3}
            y={side < 0 ? H + 1 - h : H + 1}
            width={COL * 0.6}
            height={h}
            fill={posColor(lane)}
            rx={1}
          />
        );
      })}
    </svg>
  );
}
