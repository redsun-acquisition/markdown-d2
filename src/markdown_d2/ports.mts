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

interface Port {
  shape: Shape;
  block: Shape;
  side: -1 | 1;
}

// how far a link runs straight out of a port before it bends into its route
const BEND = 40;
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

function findPorts(diagram: Diagram): Map<string, Port> {
  const ports = new Map<string, Port>();
  for (const shape of diagram.shapes) {
    const kinds = (shape.classes ?? []).filter((name) => name in SIDES);
    const kind = kinds[0];
    if (kind === undefined) continue;
    const side = SIDES[kind];
    if (side === null || side === undefined) {
      refuse(shape, "port-top and port-bottom are not supported yet; use port-left or port-right");
    }
    if (diagram.config?.layoutEngine === "elk") {
      refuse(shape, "ports need the dagre layout; remove layout-engine: elk");
    }
    const block = parentOf(diagram.shapes, shape);
    if (block === undefined) refuse(shape, "a port needs a parent block");
    if (block.type === "sequence_diagram") refuse(shape, "ports cannot sit on a sequence diagram");
    ports.set(shape.id, { shape, block, side });
  }
  return ports;
}

function joinEnd(route: Point[], port: Port, other: string, link: Connection): Point[] {
  const { shape, block, side } = port;
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

function placeOnBoard(diagram: Diagram): void {
  const ports = findPorts(diagram);
  if (ports.size === 0) return;
  for (const { shape, block, side } of ports.values()) {
    const edge = side < 0 ? block.pos.x : block.pos.x + block.width;
    // D2 refuses a shape position that is not a whole number
    shape.pos = { x: Math.round(edge - shape.width / 2), y: shape.pos.y };
  }
  for (const link of diagram.connections) {
    const src = ports.get(link.src);
    if (src !== undefined) link.route = joinEnd(link.route, src, link.dst, link);
    const dst = ports.get(link.dst);
    if (dst !== undefined)
      link.route = joinEnd([...link.route].reverse(), dst, link.src, link).reverse();
  }
}

export function placePorts(diagram: Diagram): void {
  placeOnBoard(diagram);
  for (const board of [
    ...(diagram.layers ?? []),
    ...(diagram.scenarios ?? []),
    ...(diagram.steps ?? []),
  ]) {
    placePorts(board);
  }
}
