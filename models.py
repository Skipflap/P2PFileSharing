# Data structures for users, files and peers.
# models.py

import time

class ActiveUser:
    def __init__(self, username, address, tcp_port):
        self.username = username
        self.address = address
        self.tcp_port = tcp_port
        self.last_heartbeat = time.time()

    def update_heartbeat(self):
        self.last_heartbeat = time.time()