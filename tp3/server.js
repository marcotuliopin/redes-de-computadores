const express = require("express");
const fs = require("fs");
const cors = require('cors');
const app = express();
const port = 3000;

app.use(express.static('public'));
app.use(cors());

// Load JSON data from a file
const loadData = () => {
  const lines = fs.readFileSync("scores.jsonl", "utf8");
  let data = lines.split("\n").filter(Boolean).map(JSON.parse);
  console.log(typeof(data))
  data.map( (game, index) => {
    if(game.shots_received === undefined) {
      game.shots_received = 0;
    }
    if(game.valid_shots === undefined) {
      game.valid_shots = 0;
    }
    if(game.sunk_ships === undefined) {
      game.sunk_ships = 0;
    }
  })
  return data;
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
  let aux = data.find((entry) => entry.id === gameId);
  if (aux) {
    const {id, ... game} = aux;
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
