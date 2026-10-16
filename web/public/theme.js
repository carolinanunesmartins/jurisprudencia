/* global localStorage, document */
// Applies the reader's saved light/dark choice before the page paints, so there is no flash of the
// other theme. A plain file copied as-is (not bundled): it must run before the CSS, and the CSP
// (default-src 'self') blocks inline scripts.
try {
  var t = localStorage.getItem("theme");
  if (t === "light" || t === "dark") document.documentElement.dataset.theme = t;
} catch {
  // storage unavailable: the system theme applies
}
