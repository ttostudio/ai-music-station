import "@testing-library/jest-dom/vitest";

// jsdom does not implement scrollIntoView — mock globally
Element.prototype.scrollIntoView = () => {};

// jsdom does not implement matchMedia — mock globally
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
});

// jsdom does not implement AudioContext — suppress console errors from HTMLMediaElement
window.HTMLMediaElement.prototype.load = () => {};
window.HTMLMediaElement.prototype.play = () => Promise.resolve();
window.HTMLMediaElement.prototype.pause = () => {};

// jsdom does not implement ResizeObserver — mock globally
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
} as unknown as typeof ResizeObserver;
