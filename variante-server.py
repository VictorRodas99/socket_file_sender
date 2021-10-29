import socket
import pickle
import math
import sys
import os


# IP = '192.168.0.102'
IP = 'localhost'
PORT = 3000

def transform(data):
   if data == 0:
       return "0B"

   size_name = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]

   i = int(math.floor(math.log(data, 1024)))
   p = math.pow(1024, i)
   s = round(data / p, 2)
   return "%s %s" % (s, size_name[i])


class Server():
    def __init__(self, ip, port):
        self.data = []
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(f"Server started at: {ip}:{port}...")

        connectionSuccessful = False
        while not connectionSuccessful:
            try:
                self.sock.connect((ip, port))
                print("Successful connection!")
                connectionSuccessful = True
            except:
                pass

        control = True
        while control:
            action = self.receive_action(self.sock)

            if action == "end":
                control = False
                self.sock.close()
                sys.exit("Closing server...")

    def send_files(self, index_file, sock):
        main_data = {}
        file_meta_data = []
        files = os.listdir("./")

        if index_file > len(files) or str(index_file)[0] == '-':
            self.error('The index is invalid!', sock)
        else:
            for i in range(0, len(files)):

                if (i+1) == index_file:
                    file_select = files[i]
                    main_data["name"] = file_select
                    main_data["subdirect"] = False
                    main_data["folder"] = None

                    if os.path.isfile(file_select):

                        file = open(file_select, 'rb')
                        while True:
                            meta = file.read(4096)
                            file_meta_data.append(meta)

                            if not meta:
                                file.close()
                                break

                        file_meta_data = b''.join(file_meta_data)
                        main_data["meta_data"] = file_meta_data

                        main_data_encode = pickle.dumps(main_data)
                        by_data_len = len(main_data_encode)

                        sock.sendall(pickle.dumps(by_data_len))
                        confirm = sock.recv(1024).decode()

                        if confirm == 'Received':
                            sock.sendall(main_data_encode)

                    else:
                        os.chdir(f"./{file_select}")
                        files_sub = os.listdir("./")
                        main_data["subdirect"] = True
                        main_data["folder"] = file_select
                        main_data["total_folders"] = len(files_sub)

                        for i in range(0, len(files_sub)):
                            file_element = files_sub[i]
                            main_data["name"] = file_element
                            main_data["progress"] = (i+1)

                            #---------------------------------------
                            file = open(file_element, 'rb')
                            while True:
                                meta = file.read(4096)
                                file_meta_data.append(meta)

                                if not meta:
                                    file.close()
                                    break

                            file_meta_data = b''.join(file_meta_data)
                            main_data["meta_data"] = file_meta_data

                            main_data_encode = pickle.dumps(main_data)
                            by_data_len = len(main_data_encode)

                            sock.sendall(pickle.dumps(by_data_len))
                            confirm = sock.recv(1024).decode() #---

                            if confirm == 'Received':
                                sock.sendall(main_data_encode)
                                file_meta_data = []
                            #-------------------------------------

            os.chdir("../")

    def get_size(self, index_file, sock):
        files = os.listdir("./")

        for i in range(0, len(files)):

            if index_file == (i+1):
                file = files[i]

                if os.path.isfile(file):
                    size = os.path.getsize(file)
                    size_format = transform(size)

                    self.error(f'{index_file}: {file} - {size_format}', sock)
                else:
                    folder = file
                    os.chdir(f"./{folder}")
                    files_sub = os.listdir("./")
                    size = 0
                    for i in range(0, len(files_sub)):
                        f_ = files_sub[i]
                        size = os.path.getsize(f_) + size

                    total_size = transform(size)
                    self.error(f'{index_file}: {folder} - {total_size}', sock)
                    os.chdir("../")



    def error(self, msg, sock):
        try:
            sock.sendall(pickle.dumps(len(msg)))
            confirm = sock.recv(1024).decode()

            if confirm == 'Received':
                sock.sendall(msg.encode())
        except (ConnectionResetError, ConnectionAbortedError) as e:
            pass


    def main(self, sock):
        actual = os.listdir("./")

        actual_show = f"Actual Path - {os.getcwd()}\n"
        self.data.append(actual_show)

        for i in range(0, len(actual)):
            file = actual[i]
            size = os.path.getsize(file)
            res = os.path.isfile(file)

            if res:
                self.data.append(f"{i+1} {file} - ({transform(size)})")
            else:
                self.data.append(f"{i+1} {file}/")

        code_data = pickle.dumps(self.data)
        data_len = pickle.dumps(len(code_data))

        sock.sendall(data_len)
        confirm = sock.recv(1024).decode()

        if confirm == 'Received':
            sock.sendall(code_data)
            self.data = []


    def filter(self, f_name, sock):
        files = os.listdir("./")
        long_f = len(files)

        for i in range(0, len(files)):
            file = files[i]

            if f_name in file.lower() or f_name.lower() == file.lower():
                long_f -= 1
                size = os.path.getsize(file)
                res = os.path.isfile(file)

                if res:
                    self.data.append(f"{i+1} {file} - ({transform(size)})")
                else:
                    self.data.append(f"{i+1} {file}/")


        if long_f == len(files):
            self.error("File not found!", sock)
        else:
            code_data = pickle.dumps(self.data)
            data_len = pickle.dumps(len(code_data))

            sock.sendall(data_len)
            confirm = sock.recv(1024).decode()

            if confirm == 'Received':
                sock.sendall(code_data)
                self.data = []



    def receive_action(self, sock):
        encode_action = sock.recv(1024)
        action = pickle.loads(encode_action)

        if action == "ls":
            self.main(sock)

        elif action == "..":

            try:
                os.chdir("../")
                self.main(sock)
            except FileNotFoundError:
                self.main(sock)
                self.error("You're in the main path!", sock)

        elif action[0:2] == "cd":
            cd_path = action.split(" ")[1::]
            cd_path = ' '.join(cd_path)

            try:
                os.chdir(cd_path)
                self.main(sock)
            except FileNotFoundError:
                self.error("Path not found!", sock)


        elif action[0:2] == "df":
            try:
                start = action.index("-i")+3
                index_file = int(action[start::])
                self.send_files(index_file, sock)
            except ValueError:
                self.error('Command Error!', sock)


        elif "filter" in action:
            try:
                start = action.index("-n")+3
                f_name = action[start::]
                self.filter(f_name, sock)
            except ValueError:
                self.error('Command Error!', sock)

        elif "getsize" in action:
            try:
                start = action.index("-i")+3
                index_file = int(action[start::])
                self.get_size(index_file, sock)

            except ValueError:
                self.error('Command Error!', sock)


        elif action == "help":
            self.error('help', sock)

        else:
            self.error('Command not found!', sock)

        return action


server = Server(IP, PORT)