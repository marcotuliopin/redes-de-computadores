async function fetchGameById() {
    const gameId = document.getElementById('gameIdInput').value;
    const response = await fetch(`/api/game/${gameId}`);
    const data = await response.json();
    const gameInfo = document.getElementById('gameInfo');

    if (response.ok) {
        gameInfo.innerHTML = renderGameInfo(data);
    } else {
        gameInfo.innerHTML = `<p>Game not found</p>`;
    }
}

function renderGameInfo(data) {
    return `
        <div class="game-card">
            <h3>Game ID: ${data.game_id}</h3>
            <p><strong>Last Turn:</strong> ${data.game_stats.last_turn}</p>
            <p><strong>Timestamp Auth Start:</strong> ${data.game_stats.tstamp_auth_start}</p>
            <p><strong>Servers Authenticated:</strong> ${data.game_stats.servers_authenticated.join(', ')}</p>
            <p><strong>Timestamp Auth Completion:</strong> ${data.game_stats.tstamp_auth_completion}</p>
            <p><strong>Get Cannons Received:</strong> ${data.game_stats.getcannons_received}</p>
            <p><strong>Cannons:</strong> ${data.game_stats.cannons.map(cannon => `(${cannon.join(', ')})`).join(', ')}</p>
            <p><strong>Get Turn Received:</strong> ${data.game_stats.getturn_received}</p>
            <p><strong>Ship Moves:</strong> ${data.game_stats.ship_moves}</p>
            <p><strong>Shot Received:</strong> ${data.game_stats.shot_received}</p>
            <p><strong>Valid Shots:</strong> ${data.game_stats.valid_shots}</p>
            <p><strong>Sunk Ships:</strong> ${data.game_stats.sunk_ships}</p>
            <p><strong>Escaped Ships:</strong> ${data.game_stats.escaped_ships}</p>
            <p><strong>Remaining Life on Escaped Ships:</strong> ${data.game_stats.remaining_life_on_escaped_ships}</p>
            <p><strong>Timestamp Completion:</strong> ${data.game_stats.tstamp_completion}</p>
            <p><strong>Auth:</strong> ${data.game_stats.auth}</p>
        </div>
    `;
}

async function fetchRanking(type) {
    const limit = document.getElementById('limitInput').value;
    let start = document.getElementById('startInput').value;
    const response = await fetch(`/api/rank/${type}?limit=${limit}&start=${start}`);
    const data = await response.json();
    const rankingInfo = document.getElementById('rankingInfo');
    const pagination = document.getElementById('pagination');

    if (response.ok) {
        rankingInfo.innerHTML = renderRankingInfo(data);
        pagination.innerHTML = `
            ${data.prev ? `<button onclick="fetchRankingWithParams('${type}', ${Math.max(start - limit, 0)}, ${limit})">Previous</button>` : ''}
            ${data.next ? `<button onclick="fetchRankingWithParams('${type}', ${parseInt(start) + parseInt(limit)}, ${limit})">Next</button>` : ''}
        `;
    } else {
        rankingInfo.innerHTML = `<p>Error fetching rankings</p>`;
        pagination.innerHTML = '';
    }
}

function renderRankingInfo(data) {
    return `
        <div class="ranking-card">
            <h3>Ranking: ${data.ranking}</h3>
            <p><strong>Limit:</strong> ${data.limit}</p>
            <p><strong>Start:</strong> ${data.start}</p>
            <p><strong>Games:</strong></p>
            <ul>
                ${data.games.map(gameId => `<li>Game ID: ${gameId}</li>`).join('')}
            </ul>
        </div>
    `;
}

document.getElementById('startInput').value = 1; // Alteração no valor inicial de start para 1

function fetchRankingWithParams(type, start, limit) {
    document.getElementById('startInput').value = start > 0 ? start : 1; // Verificação para garantir que start nunca seja menor que 1
    document.getElementById('limitInput').value = limit;
    fetchRanking(type);
}
