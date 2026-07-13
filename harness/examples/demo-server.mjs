#!/usr/bin/env node

import http from "node:http";

function value(flag) {
  const index = process.argv.indexOf(flag);
  return index >= 0 ? process.argv[index + 1] : undefined;
}

const name = value("--name") || process.env.PROCESS_NAME || "demo";
const port = Number.parseInt(value("--port") || process.env.PORT || "0", 10);
const laneOwner = value("--lane-owner") || process.env.LANE_ID;

if (!Number.isSafeInteger(port) || port < 1024 || !laneOwner) {
  throw new Error("demo server requires a valid port and lane owner");
}

const server = http.createServer((request, response) => {
  response.setHeader("content-type", "application/json");
  if (request.url === "/health") {
    response.end(JSON.stringify({ ok: true, name, laneOwner }));
    return;
  }
  if (request.url?.startsWith("/dev-login")) {
    response.end(JSON.stringify({ ok: true, fake: true, name, laneOwner }));
    return;
  }
  response.statusCode = 404;
  response.end(JSON.stringify({ ok: false }));
});

server.listen(port, "localhost");

function shutdown() {
  server.close(() => process.exit(0));
}

process.on("SIGTERM", shutdown);
process.on("SIGINT", shutdown);
