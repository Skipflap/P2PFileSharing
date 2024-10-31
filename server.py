# server.py

import sys
import socket
import threading
import time
from credentials import load_credentials
from protcols import decode_message, encode_message
from models import ActiveUser

if len(sys.argv) != 2:
    print("Usage: python3 server.py server_port")
    sys.exit(1)

SERVER_HOST = '127.0.0.1'
SERVER_PORT = int(sys.argv[1])
ADDRESS = (SERVER_HOST, SERVER_PORT)
BUFFER_SIZE = 1024

# Load credentials
credentials = load_credentials()
active_users = {}
lock = threading.Lock()

# Create UDP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(ADDRESS)
print("Server is running and waiting for connections...")

def handle_client_message(data, client_address):
    message = decode_message(data)
    message_type = message.get('type')
    
    if message_type == 'AUTH':
        username = message.get('username')
        password = message.get('password')
        response = {'type': 'AUTH_RESPONSE'}
        
        with lock:
            if username not in credentials:
                response['status'] = 'FAIL'
                response['reason'] = 'Username not found.'
                print(f"{client_address}: Authentication failed for unknown user '{username}'.")
            elif credentials[username] != password:
                response['status'] = 'FAIL'
                response['reason'] = 'Incorrect password.'
                print(f"{client_address}: Authentication failed for user '{username}' due to incorrect password.")
            elif username in active_users:
                response['status'] = 'FAIL'
                response['reason'] = 'User already active.'
                print(f"{client_address}: Authentication failed for user '{username}' because they are already active.")
            else:
                response['status'] = 'OK'
                # Add to active users
                active_users[username] = ActiveUser(username, client_address)
                print(f"{client_address}: User '{username}' authenticated and active.")
        
        print(f"Sending response to {client_address}: {response}")
        server_socket.sendto(encode_message(**response), client_address)
        
    elif message_type == 'HEARTBEAT':
        username = message.get('username')
        with lock:
            if username in active_users:
                active_users[username].update_heartbeat()
                print(f"Heartbeat received from '{username}'.")
            else:
                print(f"Heartbeat received from inactive user '{username}'. Ignoring.")
                
    elif message_type == 'LAP':
        username = message.get('username')
        response = {'type': 'LAP_RESPONSE'}
        
        with lock:
            if username not in active_users:
                response['status'] = 'FAIL'
                response['reason'] = 'User not authenticated'        
                print(f"{client_address}: LAP request failed for user '{username}'")
                
            else:
                peers = [user for user in active_users if user != username]
                response['status'] = 'OK'
                response['peers'] = peers
                if peers:
                    print(f"Sending list of active peers to '{username}': {peers}")
                else: 
                    print(f"Sending empty list of active peers to '{username}'")
                    
            server_socket.sendto(encode_message(**response), client_address)
                
                
def remove_inactive_users():
    while True:
        time.sleep(1)
        current_time = time.time()
        with lock:
            inactive_users = [username for username, user in active_users.items()
                              if current_time - user.last_heartbeat > 3]
            for username in inactive_users:
                del active_users[username]
                print(f"User '{username}' removed due to inactivity.")

# Start thread to remove inactive users
threading.Thread(target=remove_inactive_users, daemon=True).start()

# Main loop
while True:
    try:
        data, client_address = server_socket.recvfrom(BUFFER_SIZE)
        threading.Thread(target=handle_client_message, args=(data, client_address)).start()
    except KeyboardInterrupt:
        print("Server shutting down.")
        server_socket.close()
        sys.exit(0)