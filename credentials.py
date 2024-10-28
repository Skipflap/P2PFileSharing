# Handles loading and managing user credentials
# credentials.py

def load_credentials(filename = 'credentials.txt') :
    credentials = {}
    try:
        with open(filename, 'r') as f:
            for line in f:
                if line.strip():
                    username, password = line.strip().split(' ')
                    credentials[username] = password
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
    return credentials

