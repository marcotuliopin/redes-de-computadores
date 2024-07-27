async function fetchGameById() {
    const gameId = document.getElementById('gameIdInput').value;
    const response = await fetch(`/api/game/${gameId}`);
    const data = await response.json();
    const gameInfo = document.getElementById('gameInfo');

    if (response.ok) {
        gameInfo.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
    } else {
        gameInfo.innerHTML = `<p>Game not found</p>`;
    }
}

async function fetchRanking(type) {
    const limit = document.getElementById('limitInput').value;
    let start = document.getElementById('startInput').value;
    const response = await fetch(`/api/rank/${type}?limit=${limit}&start=${start}`);
    const data = await response.json();
    const rankingInfo = document.getElementById('rankingInfo');
    const pagination = document.getElementById('pagination');

    if (response.ok) {
        rankingInfo.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
        pagination.innerHTML = `
            <button onclick="fetchRankingWithParams('${type}', ${Math.max(start - limit, 0)}, ${limit})">Previous</button>
            <button onclick="fetchRankingWithParams('${type}', ${parseInt(start) + parseInt(limit)}, ${limit})">Next</button>
        `;
    } else {
        rankingInfo.innerHTML = `<p>Error fetching rankings</p>`;
        pagination.innerHTML = '';
    }
}

function fetchRankingWithParams(type, start, limit) {
    document.getElementById('startInput').value = start;
    document.getElementById('limitInput').value = limit;
    fetchRanking(type);
}
