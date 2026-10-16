// Tests read the shared golden files from pipeline/ (outside the Vite root); only this is needed from Node.
declare module "node:fs" {
  export function readFileSync(path: string, encoding: "utf8"): string;
}
