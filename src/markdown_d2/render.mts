import { createInterface } from "node:readline";
import type { CompileResponse, RenderOptions } from "@d2lang/d2";
import { D2 } from "@d2lang/d2";

type Files = Record<string, string>;

interface BoardsRequest {
  id: number;
  op: "boards";
  files: Files;
}

interface RenderRequest {
  id: number;
  op: "render";
  files: Files;
  board: string;
  variant: "light" | "dark";
  light_theme: number;
  dark_theme: number;
  salt: string;
}

type Request = BoardsRequest | RenderRequest;

type Reply =
  | { id: number; boards: string[] }
  | { id: number; svg: string }
  | { id: number; error: string };

interface Board {
  name: string;
  layers?: Board[];
  scenarios?: Board[];
  steps?: Board[];
}

const KINDS = ["layers", "scenarios", "steps"] as const;
const d2 = new D2();
let last: { key: string; compiled: CompileResponse } | null = null;

async function compile(files: Files): Promise<CompileResponse> {
  const key = JSON.stringify(files);
  if (last?.key !== key) {
    last = { key, compiled: await d2.compile({ fs: files, inputPath: "index.d2" }) };
  }
  return last.compiled;
}

function boardPaths(board: Board, prefix: string): string[] {
  const paths: string[] = [];
  for (const kind of KINDS) {
    for (const child of board[kind] ?? []) {
      const path = `${prefix}${kind}.${child.name}`;
      paths.push(path, ...boardPaths(child, `${path}.`));
    }
  }
  return paths;
}

async function render(request: RenderRequest): Promise<string> {
  const { diagram, renderOptions } = await compile(request.files);
  const options: RenderOptions = { ...renderOptions, noXMLTag: true, salt: request.salt };
  // theme 0 is also D2's value when the source sets none, so the setting wins over it
  const light = renderOptions.themeID || request.light_theme;
  const dark = renderOptions.darkThemeID ?? request.dark_theme;
  options.themeID = request.variant === "dark" ? dark : light;
  delete options.darkThemeID;
  if (request.board) {
    return d2.render(diagram, { ...options, target: request.board });
  }
  return d2.render({ ...diagram, layers: [], scenarios: [], steps: [] }, options);
}

async function answer(request: Request): Promise<Reply> {
  try {
    if (request.op === "boards") {
      const { diagram } = await compile(request.files);
      return { id: request.id, boards: ["", ...boardPaths(diagram as Board, "")] };
    }
    return { id: request.id, svg: await render(request) };
  } catch (error) {
    return { id: request.id, error: error instanceof Error ? error.message : String(error) };
  }
}

const lines = createInterface({ input: process.stdin });
for await (const line of lines) {
  process.stdout.write(`${JSON.stringify(await answer(JSON.parse(line) as Request))}\n`);
}
await d2.dispose();
