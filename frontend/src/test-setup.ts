import "@testing-library/jest-dom/vitest";

// jsdom does not implement scrollIntoView — mock globally
Element.prototype.scrollIntoView = () => {};

// jsdom does not implement AudioContext — suppress console errors from HTMLMediaElement
window.HTMLMediaElement.prototype.load = () => {};
window.HTMLMediaElement.prototype.play = () => Promise.resolve();
window.HTMLMediaElement.prototype.pause = () => {};
