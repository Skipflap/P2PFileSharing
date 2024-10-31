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
            # print(f"Received response from server: {response}")  # Optional: Comment out for cleaner output
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
                            if peers:
                                print("Active peers:")
                                for peer in peers:
                                    print(peer)
                            else:
                                print("No active peers.")
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
                            if files:
                                print("Published files:")
                                for file in files:
                                    print(file)
                            else:
                                print("No files published.")
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

if __name__ == '__main__':
    main()
