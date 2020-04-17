import socket


class ThreadedServer:
    CLIENT_TIMEOUT = 60 * 5
    LISTEN_QUEUE = 5

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.host, self.port))

    def listen(self):
        self.sock.listen(self.LISTEN_QUEUE)
        while True:
            conn, addr = self.sock.accept()
            print(f'{conn.getsockname()} Connected by {addr}')

            while True:
                msg = conn.recv(1024)
                print(msg)
                if msg == b'Q':
                    return True
                new_msg = b'server response...' + msg
                conn.sendall(new_msg)


HOST = '54.157.229.65'
PORT = 65432

# f = open('./Connection/log_conn_server.txt', 'a')

server = ThreadedServer(HOST, PORT)
server.listen()


