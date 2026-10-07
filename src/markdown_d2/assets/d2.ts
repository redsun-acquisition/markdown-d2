// biome-ignore lint/correctness/noUnusedVariables: it merges into the global Window
interface Window {
  markdownD2Ready?: boolean;
  document$?: { subscribe(callback: () => void): void };
}

const ZOOM_STEP = 1.25;
const SVG = "http://www.w3.org/2000/svg";
// strokes on a 24 by 24 grid, drawn in the text colour so they follow the theme
const ICONS = {
  previous: "M15 6l-6 6 6 6",
  next: "M9 6l6 6-6 6",
  fullScreen: "M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5",
  zoomIn: "M12 5v14M5 12h14",
  zoomOut: "M5 12h14",
  close: "M6 6l12 12M18 6 6 18",
} as const;

function icon(name: keyof typeof ICONS): SVGSVGElement {
  const svg = document.createElementNS(SVG, "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("aria-hidden", "true");
  const path = document.createElementNS(SVG, "path");
  path.setAttribute("d", ICONS[name]);
  svg.append(path);
  return svg;
}

function button(
  label: string,
  content: keyof typeof ICONS | { text: string },
  onClick: () => void,
): HTMLButtonElement {
  const element = document.createElement("button");
  element.type = "button";
  element.append(typeof content === "string" ? icon(content) : content.text);
  element.setAttribute("aria-label", label);
  element.addEventListener("click", onClick);
  return element;
}

function stepControls(
  boards: HTMLElement[],
  onStep: (index: number) => void,
): { controls: HTMLElement; show: (index: number) => void; current: () => number } {
  let current = 0;
  const counter = document.createElement("span");
  counter.className = "markdown-d2-counter";
  counter.setAttribute("aria-live", "polite");
  const show = (index: number): void => {
    current = (index + boards.length) % boards.length;
    const name = boards[current]?.dataset.name;
    counter.textContent = `${current + 1} / ${boards.length}${name ? ` (${name})` : ""}`;
    onStep(current);
  };
  const controls = document.createElement("div");
  controls.className = "markdown-d2-controls";
  if (boards.length > 1) {
    controls.append(
      button("Previous step", "previous", () => show(current - 1)),
      counter,
      button("Next step", "next", () => show(current + 1)),
    );
  }
  return { controls, show, current: () => current };
}

function stepWithKeys(
  element: HTMLElement,
  steps: { show: (index: number) => void; current: () => number },
): void {
  element.addEventListener("keydown", (event) => {
    if (event.key === "ArrowLeft") steps.show(steps.current() - 1);
    if (event.key === "ArrowRight") steps.show(steps.current() + 1);
  });
}

function setUpFigure(figure: HTMLElement): void {
  if (figure.dataset.ready) return;
  figure.dataset.ready = "true";
  figure.classList.add("markdown-d2-ready");
  figure.tabIndex = 0;
  const boards = Array.from(figure.querySelectorAll<HTMLElement>(":scope > .markdown-d2-board"));
  const steps = stepControls(boards, (current) => {
    for (const [i, board] of boards.entries()) {
      board.classList.toggle("markdown-d2-current", i === current);
    }
  });
  if (boards.length > 1) stepWithKeys(figure, steps);
  steps.controls.append(
    button("Open full screen", "fullScreen", () => openDialog(boards, steps.current(), steps.show)),
  );
  figure.insertBefore(steps.controls, figure.querySelector("figcaption"));
  steps.show(0);
}

function openDialog(boards: HTMLElement[], start: number, onStep: (index: number) => void): void {
  const dialog = document.createElement("dialog");
  dialog.className = "markdown-d2-dialog";
  const stage = document.createElement("div");
  stage.className = "markdown-d2-stage";
  const view = document.createElement("div");
  view.className = "markdown-d2-view";
  stage.append(view);

  let scale = 1;
  let x = 0;
  let y = 0;
  const apply = (): void => {
    view.style.transform = `translate(${x}px, ${y}px) scale(${scale})`;
  };
  const zoom = (factor: number, originX: number, originY: number): void => {
    x = originX - (originX - x) * factor;
    y = originY - (originY - y) * factor;
    scale *= factor;
    apply();
  };
  stage.addEventListener("wheel", (event) => {
    event.preventDefault();
    const box = stage.getBoundingClientRect();
    zoom(
      event.deltaY < 0 ? ZOOM_STEP : 1 / ZOOM_STEP,
      event.clientX - box.left,
      event.clientY - box.top,
    );
  });
  let dragging: { x: number; y: number } | null = null;
  stage.addEventListener("pointerdown", (event) => {
    dragging = { x: event.clientX - x, y: event.clientY - y };
    stage.setPointerCapture(event.pointerId);
  });
  stage.addEventListener("pointermove", (event) => {
    if (!dragging) return;
    x = event.clientX - dragging.x;
    y = event.clientY - dragging.y;
    apply();
  });
  stage.addEventListener("pointerup", () => (dragging = null));

  const steps = stepControls(boards, (current) => {
    view.replaceChildren(
      ...Array.from(boards[current]?.children ?? [], (child) => child.cloneNode(true)),
    );
    onStep(current);
  });
  if (boards.length > 1) stepWithKeys(dialog, steps);
  steps.controls.append(
    button("Zoom in", "zoomIn", () => zoom(ZOOM_STEP, 0, 0)),
    button("Zoom out", "zoomOut", () => zoom(1 / ZOOM_STEP, 0, 0)),
    button("Reset zoom", { text: "1:1" }, () => {
      scale = 1;
      x = 0;
      y = 0;
      apply();
    }),
    button("Close", "close", () => dialog.close()),
  );
  dialog.append(stage, steps.controls);
  dialog.addEventListener("close", () => dialog.remove());
  document.body.append(dialog);
  steps.show(start);
  apply();
  dialog.showModal();
}

function setUpFigures(): void {
  document.querySelectorAll<HTMLElement>("figure.markdown-d2").forEach(setUpFigure);
}

(function start(): void {
  if (window.markdownD2Ready) return;
  window.markdownD2Ready = true;
  if (window.document$) window.document$.subscribe(setUpFigures);
  else if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", setUpFigures);
  else setUpFigures();
})();
