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

type Transition = "none" | "fade" | "morph";

const DURATION = { fade: 250, morph: 450 } as const;

function visibleSvg(container: Element): SVGSVGElement | null {
  for (const variant of container.querySelectorAll<HTMLElement>(
    ":scope > .markdown-d2-light, :scope > .markdown-d2-dark",
  )) {
    if (getComputedStyle(variant).display !== "none") return variant.querySelector("svg");
  }
  return null;
}

function shapes(svg: SVGSVGElement): Map<string, SVGGElement> {
  // D2 marks each shape and connection with a class holding its id, which is
  // the same on every board of the diagram
  const found = new Map<string, SVGGElement>();
  for (const group of svg.querySelectorAll<SVGGElement>("g[class]:not(.shape)")) {
    const name = group.getAttribute("class");
    if (name && !found.has(name)) found.set(name, group);
  }
  return found;
}

function measure(container: Element): Map<string, DOMRect> {
  const svg = visibleSvg(container);
  const rects = new Map<string, DOMRect>();
  for (const [name, group] of svg ? shapes(svg) : [])
    rects.set(name, group.getBoundingClientRect());
  return rects;
}

function play(transition: Transition, container: Element, before: Map<string, DOMRect>): void {
  const svg = visibleSvg(container);
  if (!svg || transition === "none" || matchMedia("(prefers-reduced-motion: reduce)").matches) {
    return;
  }
  const fadeIn = (element: Element, duration: number): void => {
    element.animate([{ opacity: 0 }, { opacity: 1 }], { duration, easing: "ease-out" });
  };
  if (transition === "fade") {
    fadeIn(svg, DURATION.fade);
    return;
  }
  // a shape moves in the units of the SVG, which may be drawn smaller than its view box
  const units = svg.viewBox.baseVal.width / svg.getBoundingClientRect().width || 1;
  for (const [name, group] of shapes(svg)) {
    const old = before.get(name);
    const now = group.getBoundingClientRect();
    if (!old) {
      fadeIn(group, DURATION.morph);
      continue;
    }
    const x = (old.left - now.left) * units;
    const y = (old.top - now.top) * units;
    // a straight connection has no width or no height, which cannot scale
    const scaleX = old.width && now.width ? old.width / now.width : 1;
    const scaleY = old.height && now.height ? old.height / now.height : 1;
    if (x === 0 && y === 0 && scaleX === 1 && scaleY === 1) continue;
    group.style.transformBox = "fill-box";
    group.style.transformOrigin = "0 0";
    group.animate(
      [
        { transform: `translate(${x}px, ${y}px) scale(${scaleX}, ${scaleY})` },
        { transform: "none" },
      ],
      { duration: DURATION.morph, easing: "ease-in-out" },
    );
  }
}

function tooltipBox(host: Element): HTMLElement {
  const found = host.querySelector<HTMLElement>(":scope > .markdown-d2-tooltip");
  if (found) return found;
  const box = document.createElement("div");
  box.className = "markdown-d2-tooltip";
  box.setAttribute("role", "tooltip");
  box.hidden = true;
  host.append(box);
  return box;
}

function hoverable(container: HTMLElement, host: Element): void {
  // the page shows its own tooltip at once, so the browser's slower one goes
  for (const title of Array.from(container.querySelectorAll("svg.d2-svg > g > title"))) {
    const group = title.parentElement;
    if (group) group.dataset.tooltip = title.textContent ?? "";
    title.remove();
  }
  const box = tooltipBox(host);
  let hovered: SVGGElement | null = null;
  const clear = (): void => {
    hovered?.classList.remove("markdown-d2-hovered");
    hovered?.ownerSVGElement?.classList.remove("markdown-d2-focus");
    hovered = null;
    box.hidden = true;
  };
  container.addEventListener("pointerover", (event) => {
    const target = event.target instanceof Element ? event.target : null;
    let group = target?.closest<SVGGElement>("svg.d2-svg > g") ?? null;
    // a tooltip icon stands for the shape whose tooltip it carries
    if (group?.classList.contains("appendix-icon")) {
      const text = group.dataset.tooltip;
      group =
        Array.from(group.parentElement?.children ?? []).find(
          (sibling): sibling is SVGGElement =>
            sibling instanceof SVGGElement &&
            !sibling.classList.contains("appendix-icon") &&
            sibling.dataset.tooltip === text,
        ) ?? group;
    }
    if (group === hovered) return;
    clear();
    if (!group) return;
    hovered = group;
    group.classList.add("markdown-d2-hovered");
    group.ownerSVGElement?.classList.add("markdown-d2-focus");
    const text = group.dataset.tooltip;
    if (text) {
      box.textContent = text;
      box.hidden = false;
    }
  });
  container.addEventListener("pointermove", (event) => {
    if (box.hidden) return;
    const left = Math.min(event.clientX + 14, window.innerWidth - box.offsetWidth - 8);
    box.style.left = `${Math.max(left, 8)}px`;
    box.style.top = `${event.clientY + 18}px`;
  });
  container.addEventListener("pointerleave", clear);
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
  const transition = (figure.dataset.transition ?? "none") as Transition;
  const steps = stepControls(boards, (current) => {
    const old = figure.querySelector(":scope > .markdown-d2-current");
    const before = old ? measure(old) : null;
    for (const [i, board] of boards.entries()) {
      board.classList.toggle("markdown-d2-current", i === current);
    }
    const now = boards[current];
    if (before && now && old !== now) play(transition, now, before);
  });
  if (boards.length > 1) stepWithKeys(figure, steps);
  steps.controls.append(
    button("Open full screen", "fullScreen", () =>
      openDialog(boards, steps.current(), transition, steps.show),
    ),
  );
  figure.prepend(steps.controls);
  hoverable(figure, document.body);
  steps.show(0);
}

function openDialog(
  boards: HTMLElement[],
  start: number,
  transition: Transition,
  onStep: (index: number) => void,
): void {
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
    const before = view.childElementCount ? measure(view) : null;
    view.replaceChildren(
      ...Array.from(boards[current]?.children ?? [], (child) => child.cloneNode(true)),
    );
    if (before) play(transition, view, before);
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
  dialog.append(steps.controls, stage);
  // the tooltip lives in the dialog, which shows above everything outside it
  hoverable(view, dialog);
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
