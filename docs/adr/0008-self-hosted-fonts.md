# ADR 0008 — Self-hosted typefaces for the site's identity

Status: accepted (2026-10-15, owner asked for a visual revamp with an identity).

## Context
The site used the browser's default sans-serif. The revamp gives it a reading voice for quoted judgments and a quieter interface face. The CSP is `default-src 'self'` (SPEC §8), so fonts cannot come from a third-party CDN at runtime, and AGENTS.md rule 9 asks for an ADR for every new runtime dependency.

## Decision
- Add `@fontsource-variable/literata` (serif, designed for long-form screen reading; quotes, headings) and `@fontsource-variable/hanken-grotesk` (sans; interface text and numbers).
- Both are bundled by Vite into `web/dist` and served from the site's own origin, so the CSP is unchanged.
- Licence: SIL Open Font License 1.1 for both (redistribution in the bundle is allowed).
- Fallbacks in the font stack (`Iowan Old Style`, `Georgia`, `system-ui`) keep the text readable if a font fails to load.

## Alternatives considered
- System font stacks only: no dependency, but no identity, and the result differs a lot between platforms.
- Google Fonts at runtime: would need a CSP exception and sends every visitor's IP to a third party.

## Consequences
- About 100–200 KB of woff2 per visitor, cached; only the subsets the page's text needs are downloaded (`unicode-range`).
- Two more packages to keep up to date (Dependabot covers `web/`).
