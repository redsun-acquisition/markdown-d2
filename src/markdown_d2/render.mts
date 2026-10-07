import { createInterface } from "node:readline";
import type { RenderOptions } from "@d2lang/d2";
import { D2 } from "@d2lang/d2";

interface Request {
  id: number;
  files: Record<string, string>;
  light_theme: number;
  dark_theme: number;
  salt: string;
}

interface DrawnBoard {
  name: string;
  light: string;
  dark: string;
}

type Reply = { id: number; boards: DrawnBoard[] } | { id: number; error: string };

interface Board {
  name: string;
  layers?: Board[];
  scenarios?: Board[];
  steps?: Board[];
}

const KINDS = ["layers", "scenarios", "steps"] as const;
const PLAIN_NAME = /^[\w-]+$/;
const d2 = new D2();

function boardPaths(board: Board, prefix: string): string[] {
  const paths: string[] = [];
  for (const kind of KINDS) {
    for (const child of board[kind] ?? []) {
      // a name with a dot or a space is quoted, or D2 would split the path at it
      const name = PLAIN_NAME.test(child.name) ? child.name : JSON.stringify(child.name);
      const path = `${prefix}${kind}.${name}`;
      paths.push(path, ...boardPaths(child, `${path}.`));
    }
  }
  return paths;
}

async function draw(request: Request): Promise<DrawnBoard[]> {
  const { diagram, renderOptions } = await d2.compile({ fs: request.files, inputPath: "index.d2" });
  const { darkThemeID, ...options } = renderOptions;
  // theme 0 is also D2's value when the source sets none, so the setting wins over it
  const light = options.themeID || request.light_theme;
  const dark = darkThemeID ?? request.dark_theme;
  const top = { ...diagram, layers: [], scenarios: [], steps: [] };
  const boards: DrawnBoard[] = [];
  for (const [index, name] of ["", ...boardPaths(diagram as Board, "")].entries()) {
    // each SVG gets its own salt, so the class names its CSS selects differ
    // between boards and themes on one page
    const svg = (themeID: number, variant: string): Promise<string> => {
      const settings: RenderOptions = {
        ...options,
        noXMLTag: true,
        themeID,
        salt: `${request.salt}-${index}${variant}`,
      };
      return name ? d2.render(diagram, { ...settings, target: name }) : d2.render(top, settings);
    };
    boards.push({ name, light: await svg(light, "l"), dark: await svg(dark, "d") });
  }
  return boards;
}

async function answer(request: Request): Promise<Reply> {
  try {
    return { id: request.id, boards: await draw(request) };
  } catch (error) {
    return { id: request.id, error: error instanceof Error ? error.message : String(error) };
  }
}

const lines = createInterface({ input: process.stdin });
for await (const line of lines) {
  process.stdout.write(`${JSON.stringify(await answer(JSON.parse(line) as Request))}\n`);
}
await d2.dispose();
