import { useCallback, useEffect, useRef, useState } from "react";
import { Link, NavLink, Route, Routes, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { type Data, loadData, loadSearch, type SearchFile } from "./data";
import { messages } from "./messages.pt";
import { createIndex, type SearchIndex, validSearchFile } from "./search";
import { SearchPage } from "./SearchPage";
import { AujPage, DivergencePage, Home, MethodPage, QuestionPage, Questions } from "./pages";

type State = { status: "loading" } | { status: "error" } | { status: "ready"; data: Data };

/** The site's mark: one line that forks in two, as a divergence does. */
function Mark() {
  return (
    <svg viewBox="0 0 32 32" aria-hidden="true" className="size-7 shrink-0">
      <path
        d="M4 16 H14 L28 6 M14 16 L28 26"
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="28" cy="6" r="2.6" fill="var(--pos-0)" />
      <circle cx="28" cy="26" r="2.6" fill="var(--pos-1)" />
    </svg>
  );
}

const NAV = [
  { to: "/perguntas", label: messages.nav.questions },
  { to: "/pesquisa", label: messages.nav.search },
  { to: "/uniformizacoes", label: messages.nav.aujs },
  { to: "/metodo", label: messages.nav.method },
];

/** On a new page, start at the top (HashRouter keeps the old scroll position otherwise). */
function useScrollReset() {
  const { pathname } = useLocation();
  useEffect(() => {
    if (typeof window.scrollTo === "function" && !/jsdom/i.test(navigator.userAgent)) {
      window.scrollTo(0, 0);
    }
  }, [pathname]);
}

/** The header's search box, on every page; the query lives in the URL (/pesquisa?q=) so it can be shared. */
function SearchBox() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const fromUrl = params.get("q") ?? "";
  const [value, setValue] = useState(fromUrl);
  useEffect(() => setValue(fromUrl), [fromUrl]);
  return (
    <form
      role="search"
      aria-label={messages.search.region}
      className="flex items-center gap-2"
      onSubmit={(e) => {
        e.preventDefault();
        navigate(`/pesquisa?q=${encodeURIComponent(value.trim())}`);
      }}
    >
      <label htmlFor="pesquisa-q" className="sr-only">
        {messages.search.formLabel}
      </label>
      <input
        id="pesquisa-q"
        type="search"
        name="q"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={messages.search.placeholder}
        autoComplete="off"
        className="w-full min-w-0 sm:w-64 border border-rule bg-paper px-3 py-1.5 text-[0.95rem] rounded-[3px]"
      />
      <button type="submit" className="border border-ink rounded-[3px] px-3 py-1.5 text-sm font-semibold">
        {messages.search.submit}
      </button>
    </form>
  );
}

export function App({
  load = loadData,
  search = loadSearch,
}: {
  load?: () => Promise<Data>;
  search?: () => Promise<SearchFile>;
}) {
  const [state, setState] = useState<State>({ status: "loading" });
  // built once, on the first search; a failed search.json only means no sumário words
  const indexRef = useRef<Promise<SearchIndex> | null>(null);
  const dataRef = useRef<Data | null>(null);
  dataRef.current = state.status === "ready" ? state.data : null;
  const getIndex = useCallback(() => {
    if (!indexRef.current) {
      const empty = { questions: [], judgments: [] };
      // an unreadable search.json (failed fetch, wrong version, bad shape) means no sumário words, nothing worse
      const built = search()
        .then(validSearchFile, () => null)
        .then((file) => {
          const data = dataRef.current ?? empty;
          try {
            return createIndex(data, file);
          } catch {
            return createIndex(data, null);
          }
        });
      indexRef.current = built;
      built.catch(() => {
        indexRef.current = null; // do not cache a failure: the next search tries again
      });
    }
    return indexRef.current;
  }, [search]);
  useEffect(() => {
    let alive = true;
    load().then(
      (data) => alive && setState({ status: "ready", data }),
      () => alive && setState({ status: "error" }),
    );
    return () => {
      alive = false;
    };
  }, [load]);
  useScrollReset();

  return (
    <div className="min-h-dvh">
      <a
        href="#conteudo"
        onClick={(e) => {
          // HashRouter owns the hash: move focus instead of navigating to "#conteudo"
          e.preventDefault();
          document.getElementById("conteudo")?.focus();
        }}
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:bg-paper focus:px-3 focus:py-2"
      >
        {messages.skip}
      </a>
      <header className="mx-auto max-w-5xl px-4 sm:px-6 pt-6 pb-5 border-b border-rule">
        <div className="flex flex-wrap items-center justify-between gap-x-8 gap-y-3">
          <h1 className="font-serif text-[1.375rem] leading-none">
            <Link to="/" className="inline-flex items-center gap-2.5 no-underline">
              <Mark />
              {messages.appTitle}
            </Link>
          </h1>
          <nav aria-label={messages.nav.label}>
            <ul className="flex flex-wrap gap-x-6 gap-y-1 text-[0.95rem]">
              {NAV.map((n) => (
                <li key={n.to}>
                  <NavLink
                    to={n.to}
                    className={({ isActive }) =>
                      `no-underline py-2.5 inline-block border-b-2 ${
                        isActive ? "border-ink" : "border-transparent text-graphite hover:text-ink"
                      }`
                    }
                  >
                    {n.label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>
          <SearchBox />
        </div>
        <p role="note" className="mt-3 text-sm text-graphite">
          {messages.disclaimer}
        </p>
      </header>
      <main id="conteudo" tabIndex={-1} className="mx-auto max-w-5xl px-4 sm:px-6 py-10 sm:py-14 outline-none">
        {state.status === "loading" && <p className="text-graphite">{messages.loading}</p>}
        {state.status === "error" && <p role="alert">{messages.loadError}</p>}
        {state.status === "ready" && (
          <Routes>
            <Route path="/" element={<Home data={state.data} />} />
            <Route path="/perguntas" element={<Questions data={state.data} />} />
            <Route path="/perguntas/:id" element={<QuestionPage data={state.data} />} />
            <Route path="/uniformizacoes" element={<AujPage data={state.data} />} />
            <Route path="/divergencias/:id" element={<DivergencePage data={state.data} />} />
            <Route path="/pesquisa" element={<SearchPage getIndex={getIndex} />} />
            <Route path="/metodo" element={<MethodPage data={state.data} />} />
            <Route path="*" element={<Home data={state.data} />} />
          </Routes>
        )}
      </main>
    </div>
  );
}
