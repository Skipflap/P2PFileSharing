# PeerConnectFS

**PeerConnectFS** is a permissioned, peer-to-peer file sharing system built on a hybrid **client-server and P2P architecture**, featuring authentication, file publishing, and real-time transfers over **UDP and TCP**. The system mirrors practical peer-based networks, simulating decentralized file exchanges with a centralized indexing server.

---

##  Technologies Used

- Python 3
- `socket` module (UDP & TCP)
- `threading` for concurrent execution
- Custom application-layer protocol

---

##  Key Features

- 🔐 **User Authentication**  
  Authenticated users via a secure UDP channel using a centralized `credentials.txt` file.

- 🧭 **Central Indexing Server**  
  Tracks active users and their published files. Clients query the server to locate files.

- 🫀 **Heartbeat Mechanism**  
  Clients send heartbeat signals every 2 seconds to maintain active status. Server removes inactive users after 3 seconds of silence.

- 📂 **File Publishing & Sharing**  
  - `pub <filename>` to publish a file  
  - `get <filename>` downloads directly from another peer using TCP  
  - `unp <filename>` unpublishes a file

- 🔍 **Search & Discovery**  
  - `lap`: List all active peers  
  - `lpf`: List your published files  
  - `sch <substring>`: Search for files shared by others

- 🔄 **Multithreaded Architecture**  
  Separate threads manage:
  - User interaction
  - Heartbeat messages
  - Incoming TCP file requests
  - File transfers (upload/download)

---

##  Commands (Client)

```bash
get <filename>   # Download file from another peer
pub <filename>   # Publish a file to the network
unp <filename>   # Unpublish a file
lap              # List active peers
lpf              # List your published files
sch <substring>  # Search shared files
xit              # Exit the network
```

## 📸 Example Usage

Let's walk through a simple example using three sample users: `hans`, `vader`, and `yoda`.

### 1. Start the server

```bash
python3 server.py 50000
```

### 2. Start each client in a separate terminal

```bash
python3 client.py 50000
```

Each client will be prompted to authenticate with a username and password from `credentials.txt`.

### 3. Sample interaction

#### Hans (Uploader)
```bash
$ python3 client.py 50000
Username: hans
Password: hanspass
> pub BitTrickle.mp4
> lpf
BitTrickle.mp4
```

#### Vader (Downloader)
```bash
$ python3 client.py 50000
Username: vader
Password: vaderpass
> sch BitTrickle
BitTrickle.mp4
> get BitTrickle.mp4
Download successful: BitTrickle.mp4
```

#### Yoda (Peer Discovery)
```bash
$ python3 client.py 50000
Username: yoda
Password: yodapass
> lap
hans
vader
```

### 4. Exit the network

```bash
> xit
```

This demonstrates core features: publishing, searching, downloading, peer discovery, and session management—all within a decentralized file sharing system.
