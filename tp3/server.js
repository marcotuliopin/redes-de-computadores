const express = require("express");
const fs = require("fs");
const app = express();
const port = 3000;

app.use(express.static('public'));

// Load JSON data from a file
const loadData = () => {
  const data = fs.readFileSync("scores.jsonl", "utf8");
  return data.split("\n").filter(Boolean).map(JSON.parse);
};

const data = loadData();

// Helper function to validate and parse query parameters
const parseQueryParams = (req) => {
  const limit = parseInt(req.query.limit, 10);
  const start = parseInt(req.query.start, 10);

  if (isNaN(limit) || isNaN(start) || limit <= 0 || start < 0) {
    return { valid: false, error: "Invalid query parameters" };
  }

  if (limit > 50) {
    return { valid: false, error: "Limit cannot exceed 50" };
  }

  return { valid: true, limit, start };
};

app.get("/api/game/:id", (req, res) => {
  const gameId = parseInt(req.params.id, 10);
  const game = data.find((entry) => entry.id === gameId);
  console.log("called game id")
  if (game) {
    res.json({
      game_id: gameId,
      game_stats: game,
    });
  } else {
    res.status(404).send("Game not found");
  }
});

app.get("/api/rank/sunk", (req, res) => {
  const { valid, limit, start, error } = parseQueryParams(req);
  console.log("called sunk")
  if (!valid) {
    return res.status(400).json({ error });
  }

  const sortedData = data
    .sort((a, b) => b.sunk_ships - a.sunk_ships)
    .slice(start - 1, start - 1 + limit);

  const response = {
    ranking: "sunk",
    limit,
    start,
    games: sortedData.map((game) => game.id),
    prev:
      start > 0
        ? `/api/rank/sunk?limit=${limit}&start=${Math.max(start - limit, 0)}`
        : null,
    next:
      start + limit < data.length
        ? `/api/rank/sunk?limit=${limit}&start=${start + limit}`
        : null,
  };

  res.json(response);
});

app.get("/api/rank/escaped", (req, res) => {
  const { valid, limit, start, error } = parseQueryParams(req);
  console.log("called escaped")
  if (!valid) {
    return res.status(400).json({ error });
  }

  const sortedData = data
    .sort((a, b) => a.escaped_ships - b.escaped_ships)
    .slice(start, start + limit);

  const response = {
    ranking: "escaped",
    limit,
    start,
    games: sortedData.map((game) => game.id),
    prev:
      start > 0
        ? `/api/rank/escaped?limit=${limit}&start=${Math.max(start - limit, 0)}`
        : null,
    next:
      start + limit < data.length
        ? `/api/rank/escaped?limit=${limit}&start=${start + limit}`
        : null,
  };

  res.json(response);
});

// Server and keep-alive settings
const server = app.listen(port, () => {
  console.log(`Server is running on http://localhost:${port}`);
});

// Enable keep-alive for the server
server.keepAliveTimeout = 60000; // Keep the connection alive for 60 seconds
server.headersTimeout = 65000; // Allow 5 seconds extra for headers
