// Shapes marked as ports move onto the edge of their block once D2 has laid
// the diagram out, before it is drawn.

interface Point {
  x: number;
  y: number;
}

interface Shape {
  id: string;
  type: string;
  classes?: string[] | null;
  pos: Point;
  width: number;
  height: number;
  strokeWidth: number;
  labelWidth: number;
  labelHeight: number;
  labelPosition: string;
}

interface Connection {
  id: string;
  src: string;
  dst: string;
  route: Point[];
  isCurve?: boolean;
}

export interface Diagram {
  config?: { layoutEngine?: string | null } | null;
  shapes: Shape[];
  connections: Connection[];
  layers?: Diagram[] | null;
  scenarios?: Diagram[] | null;
  steps?: Diagram[] | null;
}

interface Box {
  left: number;
  right: number;
  top: number;
  bottom: number;
}

interface Port {
  shape: Shape;
  block: Shape;
  side: -1 | 1;
}

// how far a link runs straight out of a port before it bends into its route
const BEND = 40;
// how far past its container a link that goes around it runs at most, and the
// narrowest gap it may run through
const AROUND = 20;
const NARROWEST = 10;
// how close a link that goes around a container may come to another shape
const CLEARANCE = 4;
const NAME_SIDES: Record<string, -1 | 1> = {
  OUTSIDE_LEFT_MIDDLE: -1,
  OUTSIDE_RIGHT_MIDDLE: 1,
};
const SIDES: Record<string, -1 | 1 | null> = {
  "port-left": -1,
  "port-right": 1,
  "port-top": null,
  "port-bottom": null,
};

function refuse(port: Shape, reason: string): never {
  throw new Error(`port "${port.id}": ${reason}`);
}

function parentOf(shapes: Shape[], shape: Shape): Shape | undefined {
  let parent: Shape | undefined;
  for (const other of shapes) {
    if (shape.id.startsWith(`${other.id}.`) && other.id.length > (parent?.id.length ?? -1)) {
      parent = other;
    }
  }
  return parent;
}

function findPorts(diagram: Diagram, engine: string | null | undefined): Map<string, Port> {
  const ports = new Map<string, Port>();
  for (const shape of diagram.shapes) {
    const kinds = (shape.classes ?? []).filter((name) => name in SIDES);
    const kind = kinds[0];
    if (kind === undefined) continue;
    const side = SIDES[kind];
    if (side === null || side === undefined) {
      refuse(shape, "port-top and port-bottom are not supported yet; use port-left or port-right");
    }
    if (engine === "elk") {
      refuse(shape, "ports need the dagre layout; remove layout-engine: elk");
    }
    const block = parentOf(diagram.shapes, shape);
    if (block === undefined) refuse(shape, "a port needs a parent block");
    if (block.type === "sequence_diagram") refuse(shape, "ports cannot sit on a sequence diagram");
    ports.set(shape.id, { shape, block, side });
  }
  return ports;
}

function groupBy(ports: Iterable<Port>, key: (port: Port) => string): Port[][] {
  const groups = new Map<string, Port[]>();
  for (const port of ports) {
    const name = key(port);
    groups.set(name, [...(groups.get(name) ?? []), port]);
  }
  return [...groups.values()];
}

function checkOverlaps(ports: Map<string, Port>): void {
  for (const edge of groupBy(ports.values(), ({ block, side }) => `${side} ${block.id}`)) {
    edge.sort((a, b) => a.shape.pos.y - b.shape.pos.y);
    for (const [index, { shape, block, side }] of edge.entries()) {
      const above = edge[index - 1]?.shape;
      if (above !== undefined && shape.pos.y < above.pos.y + above.height + above.strokeWidth) {
        const name = side < 0 ? "left" : "right";
        refuse(
          shape,
          `overlaps port "${above.id}" on the ${name} edge of "${block.id}"; use direction: right and write the links between containers with --`,
        );
      }
    }
  }
}

function nameBox({ shape }: Port): Box | undefined {
  const dir = NAME_SIDES[shape.labelPosition];
  if (dir === undefined) return undefined;
  const border = shape.pos.x + shape.width / 2 + (dir * (shape.width + shape.strokeWidth)) / 2;
  const far = border + dir * shape.labelWidth;
  const middle = shape.pos.y + shape.height / 2;
  return {
    left: Math.min(border, far),
    right: Math.max(border, far),
    top: middle - shape.labelHeight / 2,
    bottom: middle + shape.labelHeight / 2,
  };
}

function checkNames(ports: Map<string, Port>): void {
  for (const group of groupBy(ports.values(), ({ block }) => block.id)) {
    const boxes: Box[] = [];
    for (const port of group) {
      const box = nameBox(port);
      if (box === undefined) continue;
      const { block, side } = port;
      const crosses =
        (side < 0 ? box.right > block.pos.x + block.width : box.left < block.pos.x) ||
        boxes.some(
          (other) =>
            box.left < other.right &&
            other.left < box.right &&
            box.top < other.bottom &&
            other.top < box.bottom,
        );
      if (crosses) {
        refuse(
          port.shape,
          `its name crosses the edge of "${block.id}" or another port's name; shorten the name`,
        );
      }
      boxes.push(box);
    }
  }
}

function occupied(shape: Shape): Box {
  const box = {
    left: shape.pos.x,
    right: shape.pos.x + shape.width,
    top: shape.pos.y,
    bottom: shape.pos.y + shape.height,
  };
  const at = String(shape.labelPosition);
  if (at.startsWith("OUTSIDE_TOP")) box.top -= shape.labelHeight;
  else if (at.startsWith("OUTSIDE_BOTTOM")) box.bottom += shape.labelHeight;
  else if (at.startsWith("OUTSIDE_LEFT")) box.left -= shape.labelWidth;
  else if (at.startsWith("OUTSIDE_RIGHT")) box.right += shape.labelWidth;
  return box;
}

function obstacles(shapes: Shape[], blocks: Shape[], ends: string[]): Box[] {
  // the link has to reach its ends, so the shapes holding them are no
  // obstacle, except the containers it goes around
  const passable = (shape: Shape) =>
    !blocks.includes(shape) &&
    ends.some((end) => end === shape.id || end.startsWith(`${shape.id}.`));
  return shapes.filter((shape) => !passable(shape)).map(occupied);
}

function blocked(path: Point[], boxes: Box[]): boolean {
  for (const [index, to] of path.entries()) {
    const from = path[index - 1];
    if (from === undefined) continue;
    const steps = Math.max(1, Math.ceil(Math.hypot(to.x - from.x, to.y - from.y) / 2));
    for (let step = 0; step <= steps; step++) {
      const x = from.x + ((to.x - from.x) * step) / steps;
      const y = from.y + ((to.y - from.y) * step) / steps;
      const hit = boxes.some(
        (box) =>
          x > box.left - CLEARANCE &&
          x < box.right + CLEARANCE &&
          y > box.top - CLEARANCE &&
          y < box.bottom + CLEARANCE,
      );
      if (hit) return true;
    }
  }
  return false;
}

function middle(a: Point, b: Point): Point {
  return { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
}

function rounded(start: Point, corners: Point[], finish: Point): Point[] {
  // one cubic per corner, from the middle of the leg before it to the middle
  // of the leg after it, with the corner as both control points
  const chain = [start];
  for (const [index, corner] of corners.entries()) {
    const next = corners[index + 1];
    chain.push(corner, corner, next === undefined ? finish : middle(corner, next));
  }
  return chain;
}

function lineAround(
  ways: number[],
  around: Box,
  boxes: Box[],
  corners: (y: number) => Point[],
): Point[] | undefined {
  const xs = corners(0).map(({ x }) => x);
  const from = Math.min(...xs);
  const to = Math.max(...xs);
  for (const way of ways) {
    const base = way > 0 ? around.bottom : around.top;
    let gap = Number.POSITIVE_INFINITY;
    for (const box of boxes) {
      if (box.right < from || box.left > to) continue;
      const distance = way > 0 ? box.top - base : base - box.bottom;
      if (distance >= 0) gap = Math.min(gap, distance);
    }
    if (gap < NARROWEST) continue;
    const line = corners(base + way * Math.min(AROUND, gap / 2));
    if (!blocked(line, boxes)) return line;
  }
  return undefined;
}

function joinAt(route: Point[], k: number): [Point, Point[]] {
  const tail = route.slice(k) as [Point, ...Point[]];
  const [anchor, after] = tail;
  // at the last point, the control before it stays, so a join made at the
  // other end of the link is kept
  const control =
    after === undefined
      ? (route[k - 1] as Point)
      : { x: 2 * anchor.x - after.x, y: 2 * anchor.y - after.y };
  return [control, tail];
}

function endOf({ shape }: Port, dir: number): Point {
  // D2 pulls each end of a drawn path back by half the shape's stroke, so a
  // route ending on the shape's box is drawn meeting the outside of its stroke
  return { x: shape.pos.x + ((1 + dir) * shape.width) / 2, y: shape.pos.y + shape.height / 2 };
}

function behind(port: Port, other: Shape): boolean {
  if (other.id.startsWith(`${port.block.id}.`)) return false;
  const x = port.shape.pos.x + port.shape.width / 2;
  return (other.pos.x + other.width / 2 - x) * port.side < 0;
}

function noRoom(port: Port, link: Connection, around: string, advice: string): never {
  refuse(port.shape, `no room to take link "${link.id}" around ${around}; ${advice}`);
}

function goAround(
  route: Point[],
  port: Port,
  other: string,
  link: Connection,
  shapes: Shape[],
): Point[] {
  const { block, side } = port;
  const back = side < 0 ? block.pos.x + block.width : block.pos.x;
  let k = 3;
  while (k < route.length - 1 && ((route[k] as Point).x - back) * -side <= AROUND) k += 3;
  const [control, tail] = joinAt(route, k);
  const anchor = tail[0] as Point;
  const end = endOf(port, side);
  const out = { x: end.x + side * BEND, y: end.y };
  // below, unless the link goes on above the container; the title sits above
  const line = lineAround(
    anchor.y < block.pos.y ? [-1, 1] : [1, -1],
    occupied(block),
    obstacles(shapes, [block], [port.shape.id, other]),
    (y) => [out, { x: out.x, y }, { x: anchor.x, y }],
  );
  if (line === undefined) {
    noRoom(port, link, `"${block.id}"`, `put the port on the ${side < 0 ? "right" : "left"} edge`);
  }
  const [, turn, across] = line as [Point, Point, Point];
  return [...rounded(end, [out, turn], middle(turn, across)), across, control, ...tail];
}

function goAroundBoth(a: Port, b: Port, link: Connection, shapes: Shape[]): Point[] {
  const start = endOf(a, a.side);
  const finish = endOf(b, b.side);
  const outA = { x: start.x + a.side * BEND, y: start.y };
  const outB = { x: finish.x + b.side * BEND, y: finish.y };
  const first = occupied(a.block);
  const second = occupied(b.block);
  const around = {
    left: Math.min(first.left, second.left),
    right: Math.max(first.right, second.right),
    top: Math.min(first.top, second.top),
    bottom: Math.max(first.bottom, second.bottom),
  };
  const line = lineAround(
    [1, -1],
    around,
    obstacles(shapes, [a.block, b.block], [a.shape.id, b.shape.id]),
    (y) => [outA, { x: outA.x, y }, { x: outB.x, y }, outB],
  );
  if (line === undefined) {
    noRoom(
      a,
      link,
      `"${a.block.id}" and "${b.block.id}"`,
      "put the ports on the edges that face each other",
    );
  }
  return rounded(start, line as Point[], finish);
}

function joinEnd(
  route: Point[],
  port: Port,
  other: string,
  link: Connection,
  shapes: Shape[],
): Point[] {
  const { shape, block, side } = port;
  if (route.length % 3 !== 1) refuse(shape, `unexpected route for connection "${link.id}"`);
  const dir = other.startsWith(`${block.id}.`) ? -side : side;
  const end = endOf(port, dir);
  let k = 3;
  while (k < route.length - 1 && ((route[k] as Point).x - end.x) * dir <= BEND) k += 3;
  const [control, tail] = joinAt(route, k);
  // a link whose other end lies behind the port would cross its container
  if (dir === side && k === route.length - 1 && ((tail[0] as Point).x - end.x) * dir < 0) {
    return goAround(route, port, other, link, shapes);
  }
  return [end, { x: end.x + dir * BEND, y: end.y }, control, ...tail];
}

function placeOnBoard(diagram: Diagram, engine: string | null | undefined): void {
  const ports = findPorts(diagram, engine);
  if (ports.size === 0) return;
  for (const { shape, block, side } of ports.values()) {
    const edge = side < 0 ? block.pos.x : block.pos.x + block.width;
    // D2 refuses a shape position that is not a whole number
    shape.pos = { x: Math.round(edge - shape.width / 2), y: shape.pos.y };
  }
  checkOverlaps(ports);
  checkNames(ports);
  for (const link of diagram.connections) {
    const src = ports.get(link.src);
    const dst = ports.get(link.dst);
    const port = src ?? dst;
    if (port === undefined) continue;
    if (link.isCurve !== true) {
      refuse(
        port.shape,
        `a port cannot have a link that runs straight, as "${link.id}" does into or out of a grid container`,
      );
    }
    // two ports that each face away from the other are joined under both containers
    if (
      src !== undefined &&
      dst !== undefined &&
      behind(src, dst.shape) &&
      behind(dst, src.shape)
    ) {
      link.route = goAroundBoth(src, dst, link, diagram.shapes);
      continue;
    }
    if (src !== undefined) link.route = joinEnd(link.route, src, link.dst, link, diagram.shapes);
    if (dst !== undefined) {
      const back = joinEnd([...link.route].reverse(), dst, link.src, link, diagram.shapes);
      link.route = back.reverse();
    }
  }
}

// only the top board carries the d2-config, so its layout engine is passed down
export function placePorts(diagram: Diagram, engine = diagram.config?.layoutEngine): void {
  placeOnBoard(diagram, engine);
  for (const board of [
    ...(diagram.layers ?? []),
    ...(diagram.scenarios ?? []),
    ...(diagram.steps ?? []),
  ]) {
    placePorts(board, engine);
  }
}
