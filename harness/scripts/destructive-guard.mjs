import { resolve } from "node:path";

function shellWords(command) {
  const words = [];
  const pattern = /"((?:\\.|[^"\\])*)"|'([^']*)'|([^\s]+)/g;
  for (const match of command.matchAll(pattern)) {
    const word = match[1] ?? match[2] ?? match[3];
    if (word) words.push(word);
  }
  return words;
}

function protectedTarget(target, protectedPaths, cwd) {
  const normalized = target.replace(/\/$/, "");
  if (!normalized || normalized === "/" || normalized === "/*") return true;
  if (/[$`]/.test(normalized)) return true;
  if (["~", "~/*", "$HOME", "${HOME}", "/Users", "/Users/*"].includes(normalized)) return true;
  if (normalized.split(/[\\/]+/).includes(".git")) return true;
  const resolvedTarget = resolve(cwd, target);
  return protectedPaths.some((path) => {
    const protectedPath = resolve(path);
    return resolvedTarget === protectedPath || normalized === `${protectedPath}/*`;
  });
}

export function isDestructiveCommand(command, protectedPaths, cwd) {
  for (const segment of command.split(/[;&|\n]/)) {
    const words = shellWords(segment.trim());
    if (words[0] === "sudo" || words[0] === "command") words.shift();
    if (words.shift() !== "rm") continue;
    let recursive = false;
    let afterOptions = false;
    const targets = [];
    for (const word of words) {
      if (!afterOptions && word === "--") {
        afterOptions = true;
      } else if (!afterOptions && word.startsWith("-")) {
        if (word === "--recursive" || /^-[^-]*r/i.test(word)) recursive = true;
      } else {
        targets.push(word);
      }
    }
    if (recursive && targets.some((target) => protectedTarget(target, protectedPaths, cwd))) return true;
  }
  return false;
}
