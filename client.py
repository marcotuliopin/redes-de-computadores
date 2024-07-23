import socket

# Create a socket object
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Get the hostname of the server (or use the IP address)
host = socket.gethostname() # Replace with your friend's actual server IP address
port = 12345  # Same port number as the server

# Connect to the server
client_socket.connect((host, port))

# Receive data from the server
message = client_socket.recv(1024).decode('utf-8')
print(f"Received from server: {message}")

# Send data to the server
client_socket.send("Hello, Server!".encode('utf-8'))

# Close the socket
client_socket.close()