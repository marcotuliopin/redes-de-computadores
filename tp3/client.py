import socket
import csv
import json

# Configuration
HOST = 'localhost'
PORT = 3000
RANK_ENDPOINT = '/api/rank/sunk'
GAME_ENDPOINT = '/api/game'
LIMIT = 50  # Set limit to maximum 50
START = 1

def create_socket():
    """Create and return a new socket."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((HOST, PORT))
        print(f"Connected to {HOST}:{PORT}")
    except Exception as e:
        print(f"Error connecting to server: {e}")
    return sock

def send_request(sock, endpoint):
    """Send an HTTP GET request and return the response."""
    request = (f"GET {endpoint} HTTP/1.1\r\n"
               f"Host: {HOST}\r\n"
               f"Connection: keep-alive\r\n"
               f"User-Agent: PythonClient\r\n"
               f"\r\n")
    try:
        sock.sendall(request.encode())
        print(f"Request sent: {request}")
    except Exception as e:
        print(f"Error sending request: {e}")
        return ""

    response = b""
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        response += chunk
    
    response_text = response.decode()
    print(f"Received response: {response_text[:500]}...")  # Print first 500 chars for debugging
    return response_text

def parse_response(response):
    """Extract JSON data from HTTP response."""
    header_end = response.find("\r\n\r\n")
    if header_end == -1:
        return {}
    body = response[header_end + 4:]
    try:
        return json.loads(body)  # Safely parse JSON
    except json.JSONDecodeError:
        print(f"Failed to parse JSON from response: {body}")
        return {}

def fetch_game_ids(sock, start):
    """Fetch game IDs from the /api/rank/sunk endpoint."""
    response = send_request(sock, f"{RANK_ENDPOINT}?limit={LIMIT}&start={start}")
    data = parse_response(response)
    game_ids = data.get('games', [])
    
    return game_ids

def fetch_all_game_ids(sock):
    """Fetch all game IDs needed for analysis."""
    all_game_ids = []
    
    # Fetch the first batch of game IDs
    game_ids = fetch_game_ids(sock, START)
    all_game_ids.extend(game_ids)
    
    # Fetch the second batch of game IDs
    game_ids = fetch_game_ids(sock, START + LIMIT)
    all_game_ids.extend(game_ids)
    
    return all_game_ids

def fetch_game_details(sock, game_id):
    """Fetch game details from the /api/game/{id} endpoint."""
    response = send_request(sock, f"{GAME_ENDPOINT}/{game_id}")
    data = parse_response(response)
    return data

def analyze_data(games):
    """Analyze data to count games and calculate average sunk ships per GAS."""
    gas_data = {}
    for game in games:
        gas = game.get('gas')  # Ensure the 'gas' field is correct
        sunk_ships = game.get('sunk_ships', 0)

        if gas not in gas_data:
            gas_data[gas] = {'count': 0, 'total_sunk': 0}
        
        gas_data[gas]['count'] += 1
        gas_data[gas]['total_sunk'] += sunk_ships

    analysis = []
    for gas, data in gas_data.items():
        count = data['count']
        average_sunk = data['total_sunk'] / count
        analysis.append((gas, count, average_sunk))
    
    analysis.sort(key=lambda x: x[1], reverse=True)
    return analysis

def save_to_csv(data, filename):
    """Save the analysis results to a CSV file."""
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['GAS', 'Number of Games', 'Average Sunk Ships'])
        writer.writerows(data)

def main():
    sock = create_socket()
    
    try:
        # Fetch all game IDs (split into two requests if necessary)
        game_ids = fetch_all_game_ids(sock)
        print(f"Game IDs: {game_ids}")
        print(f"Number of game IDs: {len(game_ids)}")

        # Fetch detailed game data
        games = []
        for game_id in game_ids:
            game_details = fetch_game_details(sock, game_id)
            if game_details:
                games.append(game_details)

        # Analyze and save results
        analysis = analyze_data(games)
        save_to_csv(analysis, 'gas_analysis.csv')
    
    finally:
        sock.close()

if __name__ == '__main__':
    main()
