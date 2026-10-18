// jsdom has no matchMedia: a fake one where the tests decide whether the system is in dark mode
const listeners = new Set();

const darkQuery = {
  matches: false,
  addEventListener: (_event, listener) => listeners.add(listener),
  removeEventListener: (_event, listener) => listeners.delete(listener),
};

// Any other query (reduced motion...) never matches
const otherQuery = { matches: false, addEventListener() {}, removeEventListener() {} };

window.matchMedia = (query) => (query === '(prefers-color-scheme: dark)' ? darkQuery : otherQuery);

// Changes the dark mode of the "system" and tells whoever is listening, like the browser does
export function setSystemDark(dark) {
  darkQuery.matches = dark;
  listeners.forEach((listener) => listener());
}
