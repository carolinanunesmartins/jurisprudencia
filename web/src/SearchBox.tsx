import { useEffect, useId, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { messages } from "./messages.pt";

const t = messages.search;
const toSearch = (q: string) => `/pesquisa?q=${encodeURIComponent(q.trim())}`;

/**
 * The search form. `compact` sits in the header on every page but the home page; the large one
 * opens the home page, with example queries one click away.
 */
export function SearchBox({ size = "compact" }: { size?: "compact" | "large" }) {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const fromUrl = params.get("q") ?? "";
  const [value, setValue] = useState(fromUrl);
  useEffect(() => setValue(fromUrl), [fromUrl]);
  const id = useId(); // two forms can share a page (header + home), so ids must not clash
  const large = size === "large";

  const form = (
    <form
      role="search"
      aria-label={t.region}
      className={`flex items-stretch gap-2 ${large ? "max-w-[40rem]" : ""}`}
      onSubmit={(e) => {
        e.preventDefault();
        navigate(toSearch(value));
      }}
    >
      <label htmlFor={id} className="sr-only">
        {t.formLabel}
      </label>
      <div className="relative flex-1 min-w-0">
        {large && (
          <svg
            viewBox="0 0 20 20"
            aria-hidden="true"
            className="pointer-events-none absolute left-3 sm:left-4 top-1/2 size-5 -translate-y-1/2 text-graphite"
          >
            <circle cx="8.5" cy="8.5" r="5.5" fill="none" stroke="currentColor" strokeWidth="1.8" />
            <path d="M12.6 12.6 17 17" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
          </svg>
        )}
        <input
          id={id}
          type="search"
          name="q"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder={large ? t.placeholderLarge : t.placeholder}
          autoComplete="off"
          className={
            large
              ? "w-full border-2 border-ink bg-paper py-3.5 pl-10 pr-3 sm:pl-12 sm:pr-4 text-base sm:text-lg rounded-[4px] shadow-[0_1px_0_var(--rule)]"
              : "w-full sm:w-64 border border-rule bg-paper px-3 py-1.5 text-[0.95rem] rounded-[3px]"
          }
        />
      </div>
      <button
        type="submit"
        className={
          large
            ? "bg-ink text-paper rounded-[4px] px-4 sm:px-5 text-base font-semibold"
            : "border border-ink rounded-[3px] px-3 py-1.5 text-sm font-semibold"
        }
      >
        {t.submit}
      </button>
    </form>
  );

  if (!large) return form;
  return (
    <div>
      {form}
      <p className="mt-3 flex flex-wrap items-center gap-x-2 gap-y-2 text-sm">
        <span className="text-graphite">{t.tryLabel}</span>
        {t.examples.map((e) => (
          <Link
            key={e}
            to={toSearch(e)}
            className="no-underline rounded-full border border-rule px-3 py-1 hover:border-ink"
          >
            {e}
          </Link>
        ))}
      </p>
    </div>
  );
}
