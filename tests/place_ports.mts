// Runs the port placement of the module named on the command line on a
// compiled diagram read from stdin, and writes the diagram or the error.
import { pathToFileURL } from "node:url";

const { placePorts } = await import(pathToFileURL(process.argv[2] ?? "").href);
let text = "";
for await (const chunk of process.stdin) text += chunk;
const diagram = JSON.parse(text);
try {
  placePorts(diagram);
  process.stdout.write(JSON.stringify({ diagram }));
} catch (error) {
  process.stdout.write(JSON.stringify({ error: error instanceof Error ? error.message : String(error) }));
}
