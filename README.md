# Freddy vs Jason Multi-Client Shell Manager

![Freddy vs Jason](https://github.com/deafbi/Friday-13th-RAT/blob/main/freddy_vs_jason.jpg)

## Description

This is a multi-client shell manager inspired by the movie "Freddy vs Jason". It allows you to remotely manage multiple client machines via a centralized server. You can execute shell commands on client machines, receive command outputs, and navigate through directories remotely.

## Features

- **Multi-client Management**: Connect and manage multiple client machines simultaneously.
- **Remote Shell Access**: Execute shell commands on connected client machines remotely.
- **Secure Communication**: Utilizes end-to-end encryption for secure communication between the server and clients.
- **Heartbeat Monitoring**: Monitors client connections with heartbeat messages to detect and handle disconnections.

## How it Works

The system consists of two main components: the server and the client.

### Server

- The server listens for incoming connections from clients on two ports: initialization port and heartbeat port.
- Upon connection, the server verifies the client's identity and stores the client's socket.
- It continuously monitors client connections and handles heartbeat messages to detect client disconnections.
- The server provides a command-line interface (CLI) for managing connected clients:
  - List all connected clients.
  - Initiate remote shells on specific clients.
  - Remove clients from the server.

### Client

- The client connects to the server on the initialization port.
- After successful initialization, it establishes a secondary connection for heartbeat messages.
- The client continuously sends heartbeat messages to the server to maintain the connection.
- It provides a remote shell interface that allows the server to execute commands on the client machine.
- The client ensures secure communication with the server using end-to-end encryption.

## Usage

1. Clone the repository: `git clone https://github.com/yourusername/yourrepositoryname.git`
2. Navigate to the server directory: `cd server`
3. Run the server script: `python3 server.py`
4. Connect the clients to the server by running the client script: `python3 client.py`
5. Follow the instructions on the server CLI to manage the connected clients.

## Dependencies

- `end2end`: Encryption library for secure communication.
- `psutil`: Process management library for Python.

## Credits

- Created by @DEAFBI

## License

This project is licensed under the [MIT License](LICENSE).
