import type { Divergence, Judgment, Position } from "./data";
import { messages } from "./messages.pt";

const FIRST = 2000;
const LAST = 2025;
const W = 720;
const LANE = 56;
const LEFT = 150;
const RIGHT = 16;
const TOP = 12;
const AXIS = 28;

// Non-colour encoding per position (SPEC §8): each lane has its own shape as well as colour.
export function Marker({ index, x, y }: { index: number; x: number; y: number }) {
  const fill = `var(--pos-${index % 4})`;
  const s = 6;
  switch (index % 4) {
    case 0:
      return <circle cx={x} cy={y} r={s} fill={fill} />;
    case 1:
      return <rect x={x - s} y={y - s} width={2 * s} height={2 * s} fill={fill} />;
    case 2:
      return <path d={`M${x},${y - s - 1} L${x + s + 1},${y + s} L${x - s - 1},${y + s} Z`} fill={fill} />;
    default:
      return <path d={`M${x},${y - s - 1} L${x + s + 1},${y} L${x},${y + s + 1} L${x - s - 1},${y} Z`} fill={fill} />;
  }
}

export function xOf(year: number): number {
  return LEFT + ((year - FIRST) / (LAST - FIRST)) * (W - LEFT - RIGHT);
}

type Props = {
  title: string;
  positions: Position[];
  judgments: Judgment[];
  divergences: Divergence[];
};

export function Timeline({ title, positions, judgments, divergences }: Props) {
  const height = TOP + positions.length * LANE + AXIS;
  const ticks = [2000, 2005, 2010, 2015, 2020, 2025];
  const seen = new Map<string, number>();
  return (
    <svg
      viewBox={`0 0 ${W} ${height}`}
      role="img"
      aria-label={messages.timelineLabel(title)}
      className="w-full h-auto"
    >
      {divergences
        .filter((d) => d.type !== "resolved")
        .map((d) => (
          <rect
            key={d.id}
            x={xOf(d.window_start - 0.5)}
            y={TOP}
            width={xOf(d.window_end + 0.5) - xOf(d.window_start - 0.5)}
            height={positions.length * LANE}
            fill="var(--color-highlight)"
          />
        ))}
      {positions.map((p, i) => {
        const y = TOP + i * LANE + LANE / 2;
        return (
          <g key={p.id}>
            <line x1={LEFT} x2={W - RIGHT} y1={y} y2={y} stroke="var(--color-rule)" />
            <Marker index={i} x={12} y={y} />
            <text x={24} y={y + 4} fontSize={12} fill="var(--color-fg)">
              {p.label.length > 20 ? `${p.label.slice(0, 19)}…` : p.label}
            </text>
          </g>
        );
      })}
      {judgments.map((j) => {
        const lane = positions.findIndex((p) => p.id === j.position);
        if (lane < 0) return null;
        const year = Number(j.date.slice(0, 4));
        const key = `${lane}-${year}`;
        const n = seen.get(key) ?? 0;
        seen.set(key, n + 1);
        const y = TOP + lane * LANE + LANE / 2 + ((n % 3) - 1) * 13;
        return (
          <g key={`${j.doc_id}-${j.question_id}`}>
            <title>{`${j.processo} · ${j.date}`}</title>
            <Marker index={lane} x={xOf(year)} y={y} />
            {j.uniformizacao && (
              <circle cx={xOf(year)} cy={y} r={10} fill="none" stroke="var(--color-fg)" strokeWidth={1.5} />
            )}
          </g>
        );
      })}
      {ticks.map((t) => (
        <text
          key={t}
          x={xOf(t)}
          y={height - 8}
          fontSize={12}
          textAnchor="middle"
          fill="var(--color-muted)"
        >
          {t}
        </text>
      ))}
    </svg>
  );
}
