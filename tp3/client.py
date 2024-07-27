import socket
import csv
import json
import sys

# Configuration
HOST = "localhost"
SUNK_RANK_ENDPOINT = "/api/rank/sunk"
ESCAPED_RANK_ENDPOINT = "/api/rank/escaped"
GAME_ENDPOINT = "/api/game"
LIMIT = 50  # Set limit to maximum 50
START = 1
SOCKET_TIMEOUT = 10  # Timeout in seconds


def create_socket(ip, port):
    """Create and return a new socket with a timeout."""
    try:
        sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        sock.connect((ip, int(port)))
    except socket.error:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, int(port)))
    sock.settimeout(100)
    return sock


def send_request(sock, endpoint):
    """Send an HTTP GET request and return the response."""
    request = (
        f"GET {endpoint} HTTP/1.1\r\n"
        f"Host: {HOST}\r\n"
        f"Connection: keep-alive\r\n"
        f"User-Agent: PythonClient\r\n"
        f"\r\n"
    )
    try:
        sock.sendall(request.encode())
    except socket.error as e:
        print(f"Error sending request: {e}")
        return "", ""

    response = b""
    try:
        while True:
            chunk = sock.recv(4096)
            response += chunk
            if b"\r\n\r\n" in response:
                break
    except socket.error as e:
        print(f"Error receiving response: {e}")
        return "", ""

    # Separate the headers from the body
    header_end = response.find(b"\r\n\r\n")
    headers = response[:header_end].decode()
    body = response[header_end + 4 :]

    # Parse headers to find Content-Length
    content_length = None
    for line in headers.split("\r\n"):
        if line.startswith("Content-Length:"):
            content_length = int(line.split(":")[1].strip())
            break

    # Receive the rest of the body if necessary
    if content_length is not None:
        while len(body) < content_length:
            chunk = sock.recv(4096)
            body += chunk

    return headers, body.decode()


def parse_response(headers, body):
    """Extract JSON data from HTTP response."""
    try:
        return json.loads(body)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return {}


def fetch_game_ids(sock, opt):
    """Fetch game IDs from the endpoint."""
    endpoint = ""
    if opt == 1:
        endpoint = SUNK_RANK_ENDPOINT
    elif opt == 2:
        endpoint = ESCAPED_RANK_ENDPOINT
    else:
        raise ValueError("Invalid option")

    headers, body = send_request(sock, f"{endpoint}?limit={LIMIT}&start={START}")
    data = parse_response(headers, body)
    game_ids = data.get("games", [])

    headers, body = send_request(
        sock, f"{endpoint}?limit={LIMIT}&start={START + LIMIT}"
    )
    data = parse_response(headers, body)
    game_ids += data.get("games", [])

    return game_ids


def fetch_game_details(sock, game_id):
    """Fetch game details from the /api/game/{id} endpoint."""
    headers, body = send_request(sock, f"{GAME_ENDPOINT}/{game_id}")
    data = parse_response(headers, body)
    return data


def analyze_data_best_gas_perf(games):
    """Analyze data to count games and calculate average sunk ships per GAS."""
    gas_data = {}
    print(len(games))
    for game in games:
        gas = game["game_stats"].get("auth")
        sunk_ships = game["game_stats"].get("sunk_ships", 0)

        if gas not in gas_data:
            gas_data[gas] = {"count": 0, "total_sunk": 0}

        gas_data[gas]["count"] += 1
        gas_data[gas]["total_sunk"] += sunk_ships

    print(len(gas_data))
    analysis = []
    for gas, data in gas_data.items():
        count = data["count"]
        average_sunk = data["total_sunk"] / count
        analysis.append((gas, count, average_sunk))

    analysis.sort(key=lambda x: x[1], reverse=True)
    return analysis


def analyze_data_best_cannon_perf(games):
    cannon_data = {}
    for game in games:
        cannons = game["game_stats"].get("cannons")
        normalized_cannons = build_normalized_cannon_placement(cannons)
        sunk_ships = game["game_stats"].get("sunk_ships", 0)
        if normalized_cannons not in cannon_data:
            cannon_data[normalized_cannons] = {"count": 0, "total_sunk": 0}
        cannon_data[normalized_cannons]["count"] += 1
        cannon_data[normalized_cannons]["total_sunk"] += sunk_ships

    analysis = []
    for cannon, data in cannon_data.items():
        count = data["count"]
        average_sunk = data["total_sunk"] / count
        analysis.append((cannon, average_sunk))

    analysis.sort(key=lambda x: x[1], reverse=False)

    return analysis


def build_normalized_cannon_placement(cannons):
    n_cannons = [0] * 5
    for _, row in cannons:
        n_cannons[row] += 1

    n_rows = [0] * 8
    normalized_cannons = ""
    for n in n_cannons:
        if n > 0:
            n_rows[n - 1] += 1
    for c in n_rows:
        normalized_cannons += str(c)

    return normalized_cannons


def save_to_csv(data, filename):
    """Save the analysis results to a CSV file."""
    with open(filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(data)


def main():
    sock = None
    # Example usage: python client.py localhost 3000 1 output.csv
    if len(sys.argv) != 5:
        print("Usage: python client.py <ip> <port> <option> <output>")

    _, ip, port, option, output = sys.argv
    global HOST
    HOST = ip
    try:
        sock = create_socket(ip, port)
        game_ids = fetch_game_ids(sock, int(option))
        games = []
        for game_id in game_ids:
            game_details = fetch_game_details(sock, game_id)
            games.append(game_details)
        if option == "1":
            analysis = analyze_data_best_gas_perf(games)
            save_to_csv(analysis, output)
        elif option == "2":
            analysis = analyze_data_best_cannon_perf(games)
            save_to_csv(analysis, output)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if sock:
            sock.close()


if __name__ == "__main__":
    main()
