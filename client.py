# client.py

import sys
import socket
import threading
import time
import os  # Import os for file existence checks
from protocols import decode_message, encode_message

if len(sys.argv) != 2:
    print("Usage: python3 client.py server_port")
    sys.exit(1)

SERVER_HOST = '127.0.0.1'
SERVER_PORT = int(sys.argv[1])
SERVER_ADDRESS = (SERVER_HOST, SERVER_PORT)
BUFFER_SIZE = 4096  # Increased buffer size to handle larger messages if needed

# Create UDP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.settimeout(5)  # Set timeout for socket operations

# Create TCP socket
tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_socket.bind((SERVER_HOST, 0))
tcp_socket.listen()
tcp_port = tcp_socket.getsockname()[1]
#print(f"TCP socket bound to port {tcp_port}")


def heartbeat(username):
    while True:
        time.sleep(2)
        message = encode_message(type='HEARTBEAT', username=username)
        client_socket.sendto(message, SERVER_ADDRESS)
        

def tcp_server():
    while True:
        conn, addr = tcp_socket.accept()
        threading.Thread(target=handle_file_request, args=(conn, addr)).start()
        

def handle_file_request(conn, addr):
    try:
        # Receive file request
        data = conn.recv(1024)
        message = decode_message(data)
        if message.get('type') == 'FILE_REQUEST':
            filename = message.get('filename')
            # Open the file and send it
            if os.path.isfile(filename):
                with open(filename, 'rb') as f:
                    # Read and send the file in chunks
                    while True:
                        bytes_read = f.read(1024)
                        if not bytes_read:
                            break
                        conn.sendall(bytes_read)
                print(f"File '{filename}' sent to {addr}")
            else:
                print(f"Requested file '{filename}' not found.")
                # Optionally, send an error message
        else:
            print(f"Received invalid file request from {addr}")
    except Exception as e:
        print(f"Error handling file request from {addr}: {e}")
    finally:
        conn.close()


def pluralize(count, singular, plural=None):
    """
    Helper function to return the singular or plural form based on the count.
    """
    if count == 1:
        return singular
    else:
        return plural if plural else singular + 's'


def main():
    authenticated = False
    username = ''
    while not authenticated:
        username = input("Enter username: ")
        password = input("Enter password: ")

        message = encode_message(type='AUTH', username=username, password=password, tcp_port=tcp_port)
        #print(f"sending AUTH message: {message}")
        client_socket.sendto(message, SERVER_ADDRESS)

        try:
            data, _ = client_socket.recvfrom(BUFFER_SIZE)
            response = decode_message(data)
            if response.get('type') == 'AUTH_RESPONSE':
                if response.get('status') == 'OK':
                    print("Welcome to BitTrickle!")
                    print("Available commands are: get, lap, lpf, pub, sch, unp, xit")
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

    # Start TCP server thread
    threading.Thread(target=tcp_server, daemon=True).start()

    # Interactive command loop
    try:
        while True:
            cmd = input("> ").strip()
            if not cmd:
                continue  # Ignore empty input

            parts = cmd.split(' ', 1)
            command = parts[0]

            if command == 'lap':
                # Send LAP request
                message = encode_message(type='LAP', username=username)
                client_socket.sendto(message, SERVER_ADDRESS)

                try:
                    data, _ = client_socket.recvfrom(BUFFER_SIZE)
                    response = decode_message(data)
                    if response.get('type') == 'LAP_RESPONSE':
                        if response.get('status') == 'OK':
                            peers = response.get('peers', [])
                            peer_count = len(peers)
                            peer_label = pluralize(peer_count, "active peer")
                            if peers:
                                print(f"{peer_count} {peer_label}:")
                                for peer in peers:
                                    print(peer)
                            else:
                                print(f"{peer_count} {peer_label}.")
                        else:
                            print(f"Failed to list active peers: {response.get('reason')}")
                    else:
                        print("Received unexpected response from server.")
                except socket.timeout:
                    print("No response from server. Please try again.")
                except Exception as e:
                    print(f"An error occurred: {e}")

            elif command == 'lpf':
                # Send LPF request
                message = encode_message(type='LPF', username=username)
                client_socket.sendto(message, SERVER_ADDRESS)

                try:
                    data, _ = client_socket.recvfrom(BUFFER_SIZE)
                    response = decode_message(data)
                    if response.get('type') == 'LPF_RESPONSE':
                        if response.get('status') == 'OK':
                            files = response.get('files', [])
                            file_count = len(files)
                            file_label = pluralize(file_count, "file published")
                            if files:
                                print(f"{file_count} {file_label}:")
                                for file in files:
                                    print(file)
                            else:
                                print(f"{file_count} {file_label}.")
                        else:
                            print(f"Failed to list published files: {response.get('reason')}")
                    else:
                        print("Received unexpected response from server.")
                except socket.timeout:
                    print("No response from server. Please try again.")
                except Exception as e:
                    print(f"An error occurred: {e}")

            elif command == 'pub':
                # Handle publish command
                if len(parts) != 2:
                    print("Usage: pub <filename>")
                    continue
                filename = parts[1]

                # Check if the file exists and is readable
                if not os.path.isfile(filename):
                    print(f"Error: File '{filename}' does not exist.")
                    continue
                if not os.access(filename, os.R_OK):
                    print(f"Error: File '{filename}' is not readable.")
                    continue

                # Send PUB request
                message = encode_message(type='PUB', username=username, filename=filename)
                client_socket.sendto(message, SERVER_ADDRESS)

                try:
                    data, _ = client_socket.recvfrom(BUFFER_SIZE)
                    response = decode_message(data)
                    if response.get('type') == 'PUB_RESPONSE':
                        if response.get('status') == 'OK':
                            print(response.get('message'))
                        else:
                            print(f"Failed to publish file: {response.get('reason')}")
                    else:
                        print("Received unexpected response from server.")
                except socket.timeout:
                    print("No response from server. Please try again.")
                except Exception as e:
                    print(f"An error occurred: {e}")

            elif command == 'unp':
                # Handle unpublish command
                if len(parts) != 2:
                    print("Usage: unp <filename>")
                    continue
                filename = parts[1]

                # Send UNP request
                message = encode_message(type='UNP', username=username, filename=filename)
                client_socket.sendto(message, SERVER_ADDRESS)

                try:
                    data, _ = client_socket.recvfrom(BUFFER_SIZE)
                    response = decode_message(data)
                    if response.get('type') == 'UNP_RESPONSE':
                        if response.get('status') == 'OK':
                            print(response.get('message'))
                        else:
                            print(f"Failed to unpublish file: {response.get('reason')}")
                    else:
                        print("Received unexpected response from server.")
                except socket.timeout:
                    print("No response from server. Please try again.")
                except Exception as e:
                    print(f"An error occurred: {e}")

            elif command == 'sch':
                # Handle search command
                if len(parts) != 2:
                    print("Usage: sch <substring>")
                    continue
                substring = parts[1]

                # Send SCH request
                message = encode_message(type='SCH', username=username, substring=substring)
                client_socket.sendto(message, SERVER_ADDRESS)

                try:
                    data, _ = client_socket.recvfrom(BUFFER_SIZE)
                    response = decode_message(data)
                    if response.get('type') == 'SCH_RESPONSE':
                        if response.get('status') == 'OK':
                            matching_files = response.get('files', [])
                            file_count = len(matching_files)
                            file_label = pluralize(file_count, "file found")
                            if matching_files:
                                print(f"{file_count} {file_label}:")
                                for file in matching_files:
                                    print(file)
                            else:
                                print(f"{file_count} {file_label}.")
                        else:
                            print(f"Failed to search files: {response.get('reason')}")
                    else:
                        print("Received unexpected response from server.")
                except socket.timeout:
                    print("No response from server. Please try again.")
                except Exception as e:
                    print(f"An error occurred: {e}")

            elif command == 'get':
                if len(parts) != 2:
                    print("Usage: get <filename>")
                    continue
                filename = parts[1]

                # Send GET request to server
                message = encode_message(type='GET', username=username, filename=filename)
                client_socket.sendto(message, SERVER_ADDRESS)

                try:
                    data, _ = client_socket.recvfrom(BUFFER_SIZE)
                    response = decode_message(data)
                    #print(f"Received GET_RESPONSE: {response}")
                    if response.get('type') == 'GET_RESPONSE':
                        if response.get('status') == 'OK':
                            # Get peer details
                            peer_ip = response.get('peer_ip')
                            peer_tcp_port = response.get('peer_tcp_port')
                            peer_username = response.get('peer_username')
                            # Connect to peer's TCP welcoming socket
                            threading.Thread(target=download_file, args=(filename, peer_ip, peer_tcp_port)).start()
                        else:
                            print(f"Failed to get file: {response.get('reason')}")
                    else:
                        print("Received unexpected response from server.")
                except socket.timeout:
                    print("No response from server. Please try again.")
                except Exception as e:
                    print(f"An error occurred: {e}")
                    
            elif command == 'xit':
                print("Goodbye!")
                client_socket.close()
                sys.exit(0)

            else:  
                print("Unknown command. Available commands are: get, lap, lpf, pub, sch, unp, xit")

    except KeyboardInterrupt:
        print("\nExiting client.")
        client_socket.close()
        sys.exit(0)


def download_file(filename, peer_ip, peer_tcp_port):
    try:
        # Create a TCP socket and connect to the peer
        #print(f"Attempting to connect to {peer_ip}:{peer_tcp_port}")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((peer_ip, int(peer_tcp_port)))
            # Send file request
            message = encode_message(type='FILE_REQUEST', filename=filename)
            s.sendall(message)
            # Open file for writing
            with open(filename, 'wb') as f:
                while True:
                    data = s.recv(1024)
                    if not data:
                        break
                    f.write(data)
            print(f"'{filename}' downloaded successfully")
    except Exception as e:
        print(f"Failed to download file '{filename}': {e}")


if __name__ == '__main__':
    main()