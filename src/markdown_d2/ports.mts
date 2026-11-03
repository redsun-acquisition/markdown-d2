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

function joinEnd(route: Point[], port: Port, other: string, link: Connection): Point[] {
  const { shape, block, side } = port;
  if (link.isCurve !== true) {
    refuse(
      shape,
      `a port cannot have a link that runs straight, as "${link.id}" does into or out of a grid container`,
    );
  }
  if (route.length % 3 !== 1) refuse(shape, `unexpected route for connection "${link.id}"`);
  const dir = other.startsWith(`${block.id}.`) ? -side : side;
  // D2 pulls each end of a drawn path back by half the shape's stroke, so a
  // route ending on the shape's box is drawn meeting the outside of its stroke
  const end = { x: shape.pos.x + ((1 + dir) * shape.width) / 2, y: shape.pos.y + shape.height / 2 };
  let k = 3;
  while (k < route.length - 1 && ((route[k] as Point).x - end.x) * dir <= BEND) k += 3;
  const tail = route.slice(k) as [Point, ...Point[]];
  const [anchor, after] = tail;
  // at the last point, the control before it stays, so a join made at the
  // other end of the link is kept
  const c2 =
    after === undefined
      ? (route[k - 1] as Point)
      : { x: 2 * anchor.x - after.x, y: 2 * anchor.y - after.y };
  return [end, { x: end.x + dir * BEND, y: end.y }, c2, ...tail];
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
    if (src !== undefined) link.route = joinEnd(link.route, src, link.dst, link);
    const dst = ports.get(link.dst);
    if (dst !== undefined)
      link.route = joinEnd([...link.route].reverse(), dst, link.src, link).reverse();
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
