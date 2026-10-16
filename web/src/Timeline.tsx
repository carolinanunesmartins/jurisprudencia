import { useEffect, useRef, useState } from "react";
import type { Divergence, Judgment, Position } from "./data";
import { DgsiLink, fmtDate } from "./links";
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

type Dot = { j: Judgment; lane: number; cx: number; cy: number };

/** Mirrored year histogram: each judgment is a dot; one position above the axis, one below. */
export function Timeline({ title, positions, judgments, divergences }: Props) {
  const cols = columns(judgments, positions);
  const rows = Math.max(1, ...cols.map((c) => Math.ceil(c.js.length / PER_ROW)));
  const half = rows * STEP + 10;
  const axis = half;
  const height = 2 * half + 4;
  const dots: Dot[] = cols.flatMap(({ lane, year, js }) =>
    js.map((j, n) => ({
      j,
      lane,
      cx: xOfYear(year) + ((n % PER_ROW) - 1) * STEP,
      cy: axis + sideOf(lane) * (8 + Math.floor(n / PER_ROW) * STEP),
    })),
  );
  const tip = useDotTip();
  return (
    <div>
      {/* the tooltip is placed in % of this box, which is exactly the SVG's (it scales with the width) */}
      <div ref={tip.boxRef} className="relative">
        <svg
          viewBox={`0 0 ${W} ${height}`}
          role="img"
          aria-label={messages.timelineLabel(title)}
          className="block w-full h-auto"
          onClick={(e) => {
            // on a phone the dots are ~3 px apart: a tap anywhere opens the nearest dot within a
            // touch target's reach (24 px); a tap right on a dot is handled by the dot itself
            if ((e.target as Element).closest("[data-testid=dot]")) return;
            const box = e.currentTarget.getBoundingClientRect();
            if (!box.width) return;
            const scale = box.width / W; // css px per chart unit
            const ux = (e.clientX - box.left) / scale;
            const uy = (e.clientY - box.top) / scale;
            let best: Dot | null = null;
            let bestDist = 24 / scale;
            for (const d of dots) {
              const dist = Math.hypot(d.cx - ux, d.cy - uy);
              if (dist < bestDist) [best, bestDist] = [d, dist];
            }
            if (best) tip.pin(best);
            else tip.close();
          }}
        >
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
          {dots.map((d) => {
            const on = tip.dot?.j === d.j;
            return (
              <g
                key={`${d.j.doc_id}-${d.j.question_id}`}
                data-testid="dot"
                className="cursor-pointer"
                onPointerEnter={() => tip.show(d)}
                onPointerLeave={tip.leave}
                onClick={() => tip.pin(d)}
              >
                <circle cx={d.cx} cy={d.cy} r={on ? R + 1.5 : R} fill={posColor(d.lane)} />
                {d.j.uniformizacao && (
                  <circle cx={d.cx} cy={d.cy} r={R + 3} fill="none" stroke="var(--ink)" strokeWidth={1.25} />
                )}
                {/* a bigger invisible target: the dots are 6 units wide */}
                <circle cx={d.cx} cy={d.cy} r={STEP / 2 + 0.5} fill="transparent" />
              </g>
            );
          })}
          {TICKS.map((t) => (
            <line key={t} x1={xOfYear(t)} x2={xOfYear(t)} y1={axis - 3} y2={axis + 3} stroke="var(--ink)" />
          ))}
        </svg>
        {tip.dot && (
          <DotTip
            dot={tip.dot}
            label={positions[tip.dot.lane]?.label ?? tip.dot.j.position}
            height={height}
            pinned={tip.pinned}
            onEnter={tip.keep}
            onLeave={tip.leave}
            onClose={tip.close}
          />
        )}
      </div>
      <YearAxis />
    </div>
  );
}

/**
 * Which dot's tooltip is open. Hover shows it; moving onto the tooltip keeps it (so its link can be
 * clicked); a click or tap pins it until Escape, the close button or a click elsewhere.
 */
function useDotTip() {
  const [dot, setDot] = useState<Dot | null>(null);
  const [pinned, setPinned] = useState(false);
  const timer = useRef<number | undefined>(undefined);
  const boxRef = useRef<HTMLDivElement>(null);
  const keep = () => window.clearTimeout(timer.current);
  const close = () => {
    window.clearTimeout(timer.current);
    setDot(null);
    setPinned(false);
  };
  useEffect(() => {
    if (!dot) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
    };
    const onDown = (e: PointerEvent) => {
      if (pinned && boxRef.current && !boxRef.current.contains(e.target as Node)) close();
    };
    document.addEventListener("keydown", onKey);
    document.addEventListener("pointerdown", onDown);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("pointerdown", onDown);
    };
  }, [dot, pinned]);
  useEffect(() => () => window.clearTimeout(timer.current), []);
  return {
    dot,
    pinned,
    boxRef,
    keep,
    close,
    show: (d: Dot) => {
      if (pinned) return;
      keep();
      setDot(d);
    },
    leave: () => {
      if (pinned) return;
      keep();
      timer.current = window.setTimeout(() => setDot(null), 250);
    },
    pin: (d: Dot) => {
      keep();
      setDot(d);
      setPinned(true);
    },
  };
}

function DotTip({
  dot,
  label,
  height,
  pinned,
  onEnter,
  onLeave,
  onClose,
}: {
  dot: Dot;
  label: string;
  height: number;
  pinned: boolean;
  onEnter: () => void;
  onLeave: () => void;
  onClose: () => void;
}) {
  const t = messages.timelineTip;
  const x = (dot.cx / W) * 100;
  const y = (dot.cy / height) * 100;
  // above the dot for the upper position, below for the lower one; kept inside the chart at the edges
  const above = dot.cy < height / 2;
  const tx = x < 18 ? "-12%" : x > 82 ? "-88%" : "-50%";
  return (
    <div
      role="dialog"
      aria-label={t.label(fmtDate(dot.j.date))}
      onPointerEnter={onEnter}
      onPointerLeave={onLeave}
      className="absolute z-10 w-60 rounded-[4px] border border-ink bg-paper px-3 py-2.5 text-sm shadow-[0_4px_16px_color-mix(in_srgb,var(--ink)_18%,transparent)]"
      style={{
        left: `${x}%`,
        top: `${y}%`,
        transform: `translate(${tx}, ${above ? "calc(-100% - 12px)" : "12px"})`,
      }}
    >
      <p className="flex items-start justify-between gap-2">
        <span className="text-graphite tabular">{fmtDate(dot.j.date)}</span>
        {pinned && (
          <button
            type="button"
            onClick={onClose}
            aria-label={t.close}
            className="-mr-1 -mt-1 size-6 leading-none text-graphite hover:text-ink"
          >
            ×
          </button>
        )}
      </p>
      <p className="font-semibold" style={{ color: posColor(dot.lane) }}>
        {label}
      </p>
      {dot.j.uniformizacao && <p className="text-graphite">{messages.uniformizacao}</p>}
      <p className="mt-1.5 text-xs text-graphite tabular break-all">{dot.j.processo}</p>
      <p className="mt-1">
        <DgsiLink url={dot.j.url}>{t.open}</DgsiLink>
      </p>
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
