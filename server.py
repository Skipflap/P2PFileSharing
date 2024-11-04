# server.py

import sys
import socket
import threading
import time
from datetime import datetime  # Import datetime for timestamping
from credentials import load_credentials
from protocols import decode_message, encode_message
from models import ActiveUser

if len(sys.argv) != 2:
    print("Usage: python3 server.py server_port")
    sys.exit(1)

SERVER_HOST = "127.0.0.1"
SERVER_PORT = int(sys.argv[1])
ADDRESS = (SERVER_HOST, SERVER_PORT)
BUFFER_SIZE = 4096  # Increased buffer size to handle larger messages if needed

# Load credentials
credentials = load_credentials()
active_users = {}
user_published_files = {}  # Dictionary to store published files per user
file_to_users = {}  # Dictionary to map filenames to set of usernames who published them
lock = threading.Lock()

# Create UDP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(ADDRESS)
print("Server is running and waiting for connections...")


def get_timestamp():
    """
    Returns the current time formatted as HH:MM:SS.mmm
    """
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def handle_client_message(data, client_address):
    message = decode_message(data)
    message_type = message.get("type")
    client_port = client_address[1]
    timestamp = get_timestamp()

    if message_type == "AUTH":
        username = message.get("username")
        password = message.get("password")
        tcp_port = message.get("tcp_port")
        response = {"type": "AUTH_RESPONSE"}

        with lock:
            if username not in credentials:
                response["status"] = "FAIL"
                response["reason"] = "Username not found."
                print(f"{timestamp}: {client_port}: Authentication failed for unknown user '{username}'.")
            elif credentials[username] != password:
                response["status"] = "FAIL"
                response["reason"] = "Incorrect password."
                print(f"{timestamp}: {client_port}: Authentication failed for user '{username}' due to incorrect password.")
            elif username in active_users:
                response["status"] = "FAIL"
                response["reason"] = "User already active."
                print(f"{timestamp}: {client_port}: Authentication failed for user '{username}' because they are already active.")
            else:
                response["status"] = "OK"
                # Add to active users
                active_users[username] = ActiveUser(username, client_address, tcp_port)
                print(f"{timestamp}: {client_port}: User '{username}' authenticated and active.")

        server_socket.sendto(encode_message(**response), client_address)

    elif message_type == "HEARTBEAT":
        username = message.get("username")
        with lock:
            if username in active_users:
                active_users[username].update_heartbeat()
                print(f"{timestamp}: {client_port}: Heartbeat received from '{username}'.")

    elif message_type == "LAP":
        username = message.get("username")
        response = {"type": "LAP_RESPONSE"}

        with lock:
            if username not in active_users:
                response["status"] = "FAIL"
                response["reason"] = "User not authenticated."
                print(f"{timestamp}: {client_port}: LAP request failed for user '{username}' - not authenticated.")
            else:
                peers = [user for user in active_users if user != username]
                response["status"] = "OK"
                response["peers"] = peers
                peer_count = len(peers)
                if peers:
                    print(f"{timestamp}: {client_port}: LAP from '{username}': {peer_count} active peer{'s' if peer_count !=1 else ''}.")
                else:
                    print(f"{timestamp}: {client_port}: LAP from '{username}': No active peers.")

        server_socket.sendto(encode_message(**response), client_address)

    elif message_type == "LPF":
        username = message.get("username")
        response = {"type": "LPF_RESPONSE"}

        with lock:
            if username not in active_users:
                response["status"] = "FAIL"
                response["reason"] = "User not authenticated."
                print(f"{timestamp}: {client_port}: LPF request failed for user '{username}' - not authenticated.")
            else:
                files = list(user_published_files.get(username, []))  # Fetch published files
                file_count = len(files)
                if files:
                    response["status"] = "OK"
                    response["files"] = files
                    print(f"{timestamp}: {client_port}: LPF from '{username}': {file_count} file{'s' if file_count !=1 else ''} published.")
                else:
                    response["status"] = "OK"
                    response["files"] = []
                    print(f"{timestamp}: {client_port}: LPF from '{username}': No files published.")

        server_socket.sendto(encode_message(**response), client_address)

    elif message_type == "PUB":
        username = message.get("username")
        filename = message.get("filename")
        response = {"type": "PUB_RESPONSE"}

        with lock:
            if username not in active_users:
                response["status"] = "FAIL"
                response["reason"] = "User not authenticated."
                print(f"{timestamp}: {client_port}: PUB request failed for user '{username}' - not authenticated.")
            else:
                if username not in user_published_files:
                    user_published_files[username] = set()
                if filename in user_published_files[username]:
                    response["status"] = "OK"
                    response["message"] = "File published successfully."
                    print(f"{timestamp}: {client_port}: User '{username}' attempted to publish '{filename}' which is already published.")
                else:
                    user_published_files[username].add(filename)
                    # Update file_to_users mapping
                    if filename not in file_to_users:
                        file_to_users[filename] = set()
                    file_to_users[filename].add(username)
                    response["status"] = "OK"
                    response["message"] = "File published successfully."
                    print(f"{timestamp}: {client_port}: User '{username}' published file '{filename}'.")

        server_socket.sendto(encode_message(**response), client_address)

    elif message_type == "SCH":
        username = message.get("username")
        substring = message.get("substring")
        response = {"type": "SCH_RESPONSE"}

        with lock:
            if username not in active_users:
                response["status"] = "FAIL"
                response["reason"] = "User not authenticated."
                print(f"{timestamp}: {client_port}: SCH request failed for user '{username}' - not authenticated.")
            else:
                # Step 1: Collect all files containing the substring
                all_matching_files = set()
                for file, users in file_to_users.items():
                    if substring in file:
                        all_matching_files.add(file)

                # Step 2: Exclude any files published by the querying user
                user_files = user_published_files.get(username, set())
                filtered_files = all_matching_files - user_files

                # Step 3: From the remaining files, include only those published by at least one active user
                final_matching_files = []
                for file in filtered_files:
                    publishers = file_to_users.get(file, set())
                    # Check if at least one publisher is active
                    if any(publisher in active_users for publisher in publishers):
                        final_matching_files.append(file)

                file_count = len(final_matching_files)
                response["status"] = "OK"
                response["files"] = final_matching_files
                if final_matching_files:
                    print(f"{timestamp}: {client_port}: SCH from '{username}': {file_count} file{'s' if file_count !=1 else ''} found.")
                else:
                    print(f"{timestamp}: {client_port}: SCH from '{username}': No matching files found.")

        server_socket.sendto(encode_message(**response), client_address)

    elif message_type == "UNP":
        username = message.get("username")
        filename = message.get("filename")
        response = {"type": "UNP_RESPONSE"}

        with lock:
            if username not in active_users:
                response["status"] = "FAIL"
                response["reason"] = "User not authenticated."
                print(f"{timestamp}: {client_port}: UNP request failed for user '{username}' - not authenticated.")
            else:
                if (
                    username in user_published_files
                    and filename in user_published_files[username]
                ):
                    user_published_files[username].remove(filename)
                    # Update file_to_users mapping
                    if filename in file_to_users:
                        file_to_users[filename].discard(username)
                        if not file_to_users[filename]:
                            del file_to_users[filename]
                    response["status"] = "OK"
                    response["message"] = "File unpublished successfully."
                    print(f"{timestamp}: {client_port}: User '{username}' unpublished file '{filename}'.")
                else:
                    response["status"] = "FAIL"
                    response["reason"] = "File not found."
                    print(f"{timestamp}: {client_port}: User '{username}' attempted to unpublish non-existent file '{filename}'.")

        server_socket.sendto(encode_message(**response), client_address)
        
    elif message_type == "GET":
        username = message.get('username')
        filename = message.get('filename')
        response = {'type': 'GET_RESPONSE'}
        
        with lock:
            if username not in active_users:
                response['status'] = 'FAIL'
                response['reason'] = 'User not authenticated.'
                print(f"{timestamp}: {client_port}: GET request failed for user '{username}' - not authenticated.")
            else:
                # Find active peers that have published the file
                peers_with_file = []
                for user, files in user_published_files.items():
                    if user != username and filename in files and user in active_users:
                        peer_user = active_users[user]
                        peers_with_file.append(peer_user)
                if peers_with_file:
                    # Select one peer arbitrarily
                    selected_peer = peers_with_file[0]
                    response['status'] = 'OK'
                    response['peer_username'] = selected_peer.username
                    response['peer_ip'] = selected_peer.address[0]  # IP address
                    response['peer_tcp_port'] = selected_peer.tcp_port  # TCP port
                    print(f"{timestamp}: {client_port}: User '{username}' requested file '{filename}'. Provided peer '{selected_peer.username}'.")
                else:
                    response['status'] = 'FAIL'
                    response['reason'] = 'No active peers have the requested file.'
                    print(f"{timestamp}: {client_port}: User '{username}' requested file '{filename}', but no active peers have it.")
                    
        print(f"{timestamp}: {client_port}: Sending GET_RESPONSE to {client_address}: {response}")
        server_socket.sendto(encode_message(**response), client_address)
        
    else:
        print(f"{timestamp}: {client_port}: Received unknown message type from {client_address}: {message_type}")
        # Optionally, send an error response


def remove_inactive_users():
    while True:
        time.sleep(1)
        current_time = time.time()
        with lock:
            inactive_users = [
                username
                for username, user in active_users.items()
                if current_time - user.last_heartbeat > 3
            ]
            for username in inactive_users:
                del active_users[username]
                print(f"{get_timestamp()}: User '{username}' removed due to inactivity.")


# Start thread to remove inactive users
threading.Thread(target=remove_inactive_users, daemon=True).start()

# Main loop
while True:
    try:
        data, client_address = server_socket.recvfrom(BUFFER_SIZE)
        threading.Thread(
            target=handle_client_message, args=(data, client_address)
        ).start()
    except KeyboardInterrupt:
        print("Server shutting down.")
        server_socket.close()
        sys.exit(0)