import type { ReactNode } from "react";
import { messages } from "./messages.pt";

// Shared by the pages and the chart (the chart cannot import pages.tsx, which imports it).

/** "2019-10-29" -> "29 out. 2019" (browsers format pt-PT short dates as 29/10/2019). */
export function fmtDate(iso: string): string {
  const [y, m, d] = iso.split("-").map(Number);
  const month = m ? messages.months[m - 1] : undefined;
  return y && month && d ? `${d} ${month} ${y}` : iso;
}

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
