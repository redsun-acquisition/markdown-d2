interface MarkdownD2Window extends Window {
  markdownD2Ready?: boolean;
  document$?: { subscribe(callback: () => void): void };
}

const ZOOM_STEP = 1.25;

function button(label: string, text: string, onClick: () => void): HTMLButtonElement {
  const element = document.createElement("button");
  element.type = "button";
  element.textContent = text;
  element.setAttribute("aria-label", label);
  element.addEventListener("click", onClick);
  return element;
}

function setUpFigure(figure: HTMLElement): void {
  if (figure.dataset.ready) return;
  figure.dataset.ready = "true";
  figure.classList.add("markdown-d2-ready");
  figure.tabIndex = 0;
  const boards = Array.from(figure.querySelectorAll<HTMLElement>(":scope > .markdown-d2-board"));
  let current = 0;
  const counter = document.createElement("span");
  counter.className = "markdown-d2-counter";
  counter.setAttribute("aria-live", "polite");

  const show = (index: number): void => {
    current = (index + boards.length) % boards.length;
    boards.forEach((board, i) => board.classList.toggle("markdown-d2-current", i === current));
    const name = boards[current].dataset.name;
    counter.textContent = `${current + 1} / ${boards.length}${name ? ` · ${name}` : ""}`;
  };

  const controls = document.createElement("div");
  controls.className = "markdown-d2-controls";
  if (boards.length > 1) {
    controls.append(
      button("Previous step", "◀", () => show(current - 1)),
      counter,
      button("Next step", "▶", () => show(current + 1)),
    );
    figure.addEventListener("keydown", (event) => {
      if (event.key === "ArrowLeft") show(current - 1);
      if (event.key === "ArrowRight") show(current + 1);
    });
  }
  controls.append(button("Open full screen", "⛶", () => openDialog(boards[current])));
  const caption = figure.querySelector("figcaption");
  figure.insertBefore(controls, caption);
  show(0);
}

function openDialog(board: HTMLElement): void {
  const dialog = document.createElement("dialog");
  dialog.className = "markdown-d2-dialog";
  const stage = document.createElement("div");
  stage.className = "markdown-d2-stage";
  const view = document.createElement("div");
  view.className = "markdown-d2-view";
  view.append(...Array.from(board.children).map((child) => child.cloneNode(true)));
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
    zoom(event.deltaY < 0 ? ZOOM_STEP : 1 / ZOOM_STEP, event.clientX - box.left, event.clientY - box.top);
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

  const controls = document.createElement("div");
  controls.className = "markdown-d2-controls";
  controls.append(
    button("Zoom in", "+", () => zoom(ZOOM_STEP, 0, 0)),
    button("Zoom out", "-", () => zoom(1 / ZOOM_STEP, 0, 0)),
    button("Reset zoom", "1:1", () => {
      scale = 1;
      x = 0;
      y = 0;
      apply();
    }),
    button("Close", "✕", () => dialog.close()),
  );
  dialog.append(stage, controls);
  dialog.addEventListener("close", () => dialog.remove());
  document.body.append(dialog);
  apply();
  dialog.showModal();
}

function setUpFigures(): void {
  document.querySelectorAll<HTMLElement>("figure.markdown-d2").forEach(setUpFigure);
}

(function start(): void {
  const page = window as MarkdownD2Window;
  if (page.markdownD2Ready) return;
  page.markdownD2Ready = true;
  if (page.document$) page.document$.subscribe(setUpFigures);
  else if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", setUpFigures);
  else setUpFigures();
})();
