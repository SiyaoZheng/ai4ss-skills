#!/usr/bin/env node
import process from "node:process";

const SECRET_KEY_RE = /(?:password|token|secret|api[_-]?key|access[_-]?key)/i;

function redact(value, key = "") {
  if (Array.isArray(value)) return value.map((item) => redact(item));
  if (!value || typeof value !== "object") {
    if (key && SECRET_KEY_RE.test(key) && typeof value === "string" && value) {
      return "[REDACTED]";
    }
    return value;
  }
  const out = {};
  for (const [childKey, childValue] of Object.entries(value)) {
    out[childKey] = redact(childValue, childKey);
  }
  return out;
}

let input = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => {
  input += chunk;
});
process.stdin.on("end", () => {
  try {
    const parsed = JSON.parse(input);
    process.stdout.write(`${JSON.stringify(redact(parsed), null, 2)}\n`);
  } catch {
    const redacted = input.replace(
      /("(?:[^"\\]|\\.)*(?:password|token|secret|api[_-]?key|access[_-]?key)(?:[^"\\]|\\.)*"\s*:\s*")([^"]*)(")/gi,
      "$1[REDACTED]$3",
    );
    process.stdout.write(redacted);
  }
});
