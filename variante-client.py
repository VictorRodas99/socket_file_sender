import socket
import pickle
import sys
import os


# HOST = '192.168.0.102'
HOST = 'localhost'
PORT = 3000


class Client():
    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((host, port))
        self.sock.listen(1)


        conn, addr = self.sock.accept()
        print(f"Connection started with {addr}...")
        self.start(self.sock)

        control = True
        while control:
            action = input("\n> ")
            self.send_action(action, conn)

    def help(self):
        print("\nActions\n")
        print("ls: show all the folders and files in the path")
        print("cd: change the directory")
        print("..: go back to the previous path")
        print("df: download a file (df -i <index of file>)")
        print("filter: <filter -n name of file>")
        print("help: shows all the commands")
        print("end: to kill the server")

    def download(self, dic_data):
        script_name = os.path.basename(__file__)
        script_path = os.path.realpath(__file__)
        script_path = script_path.replace(script_name, '')

        file_name = dic_data["name"]
        meta_data = dic_data["meta_data"]
        final_path = f'{script_path}downloads/'

        try:
            os.chdir(final_path)
        except FileNotFoundError:
            os.makedirs("downloads")

        if dic_data["subdirect"]:
            try:
                os.chdir(f'{final_path}{dic_data["folder"]}/')

            except FileNotFoundError:
                os.makedirs(dic_data["folder"])
                os.chdir(f'{final_path}{dic_data["folder"]}/')

            progress = round(dic_data["progress"] * 100 / dic_data["total_folders"])

            with open(f'{final_path}{dic_data["folder"]}/{file_name}', 'wb') as f:
                f.write(meta_data)
                sys.stdout.write("\r%d %%" % progress)
                sys.stdout.flush()

                if progress == 100:
                    print("\nDowloaded!")

        else:
            with open(f'{final_path}{file_name}', 'wb') as f:
                f.write(meta_data)
                print("Downloaded!")



    def show_d(self, msg):
        for i in range(0, len(msg)):
            if i == 0:
                if "path" in msg[i]:
                    print(f"\nActual path - {msg[i]}\n")
                else:
                    print(msg[i])
            else:
                print(msg[i])


    def start(self, sock):
        path = sys.argv
        self.help()

        try:
            final_path = path[1]
            self.send_action(final_path, sock)
        except IndexError:
            pass


    def get_data(self, c, long_data, parts, sock):
        while True:
            c += 1

            if c == 1:
                encoded_long = sock.recv(4096)
                long = pickle.loads(encoded_long)
                long = int(long)
                sock.sendall('Received'.encode())
            else:
                packet = sock.recv(4096)
                long_data = len(packet) + long_data

                if long_data == long:
                    parts.append(packet)
                    break
                else:
                    parts.append(packet)

        return parts


    def send_action(self, action, sock):
        encoded_action = pickle.dumps(action)
        sock.sendall(encoded_action)

        if action == "end":
            sock.close()
            sys.exit("Connection ended")


        if action[0:2] != "df":
            parts = self.get_data(0, 0, [], sock)

            try:
                msg_normal_received = pickle.loads(b"".join(parts))
            except:
                msg_normal_received = parts[0].decode()


        if action == "ls":
            self.show_d(msg_normal_received)

        elif action == "..":
            self.show_d(msg_normal_received)

        elif action[0:2] == "cd":
            if msg_normal_received == "Path not found!":
                print(msg_normal_received)
            else:
                self.show_d(msg_normal_received)

        elif action[0:2] == "df":
            try:
                parts = self.get_data(0, 0, [], sock)
                msg_normal_received = pickle.loads(b"".join(parts))

                dic_data = msg_normal_received

                if dic_data["subdirect"]:
                    num_total_files = (dic_data["total_folders"]-1)
                    self.download(dic_data)

                    for i in range(0, num_total_files):
                        parts = self.get_data(0, 0, [], sock)
                        dic_data = pickle.loads(b"".join(parts))

                        self.download(dic_data)
                else:
                    self.download(dic_data)

            except TypeError:
                print(msg_normal_received)


        elif action == "help":
            self.help()

        elif "filter" in action:
            if msg_normal_received == "File not found!":
                print(msg_normal_received)
            else:
                self.show_d(msg_normal_received)

        else:
            print("Command not found!")


client = Client(HOST, PORT)