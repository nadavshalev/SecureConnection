from Connection import ConnSecureServer, ConnSocketServer, ConnP2PServer
import socket
import threading


class ThreadedServer:
    CLIENT_TIMEOUT = 60 * 5
    LISTEN_QUEUE = 5

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.host, self.port))
        self.conn_dict = dict()

    def listen(self):
        self.sock.listen(self.LISTEN_QUEUE)
        while True:
            conn, addr = self.sock.accept()
            print(f'{conn.getsockname()} Connected by {addr}')
            # conn.settimeout(self.CLIENT_TIMEOUT)
            threading.Thread(target=self.proccess_client, args=(conn, addr)).start()

    def proccess_client(self, conn, addr):
        obj_sock = ConnSocketServer(conn, f, addr)
        obj_secure = ConnSecureServer(obj_sock, f)
        obj_p2p = ConnP2PServer(obj_secure, self.conn_dict, f)

        obj_p2p.start()


DEBUG = True

if DEBUG:
    LOG_TYPE = 'a'
    IP = '127.0.0.1'
else:
    LOG_TYPE = 'w'
    IP = ''

PORT = 65432

f = open('./serverLog.log', 'a')

server = ThreadedServer(IP, PORT)
server.listen()
