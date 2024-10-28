# client.py

import sys
import socket
import threading
import time
from protcols import decode_message, encode_message

if len(sys.argv) != 2:
    print("Usage: python3 client.py server_port")
    sys.exit(1)

SERVER_HOST = '127.0.0.1'
SERVER_PORT = int(sys.argv[1])
SERVER_ADDRESS = (SERVER_HOST, SERVER_PORT)
BUFFER_SIZE = 1024

# Create UDP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.settimeout(5)  # Set timeout for socket operations

def heartbeat(username):
    while True:
        time.sleep(2)
        message = encode_message(type='HEARTBEAT', username=username)
        client_socket.sendto(message, SERVER_ADDRESS)

def main():
    authenticated = False
    username = ''
    while not authenticated:
        username = input("Enter username: ")
        password = input("Enter password: ")

        message = encode_message(type='AUTH', username=username, password=password)
        client_socket.sendto(message, SERVER_ADDRESS)

        try:
            data, _ = client_socket.recvfrom(BUFFER_SIZE)
            response = decode_message(data)
            print(f"Received response from server: {response}")
            if response.get('type') == 'AUTH_RESPONSE':
                if response.get('status') == 'OK':
                    print("Welcome to BitTrickle!")
                    authenticated = True
                else:
                    print(f"Authentication failed: {response.get('reason')}")
        except socket.timeout:
            print("No response from server. Retrying...")
        except Exception as e:
            print(f"An error occurred: {e}")
            break

    if not authenticated:
        print("Failed to authenticate. Exiting.")
        client_socket.close()
        sys.exit(0)

    # Start heartbeat thread
    threading.Thread(target=heartbeat, args=(username,), daemon=True).start()

    # For testing purposes, keep the client running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting client.")
        client_socket.close()
        sys.exit(0)

if __name__ == '__main__':
    main()