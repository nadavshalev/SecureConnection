import socket
from Connection.ConnSecure import ConnSecureServer
from Connection.ConnSocket import ConnSocketServer
import socket
import threading

class ThreadedServer:
	def __init__(self, host, port):
		self.host = host
		self.port = port
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.bind((self.host, self.port))

	def listen(self):
		self.sock.listen(5)
		while True:
			conn, addr = self.sock.accept()
			print('Connected by', addr)
			conn.settimeout(60)
			threading.Thread(target=self.proccess_client, args=(conn, addr)).start()

	def proccess_client(self, conn, addr):
		obj_sock = ConnSocketServer(conn, f, addr)
		obj_secure = ConnSecureServer(obj_sock, f)

		if not obj_secure.connect():
			print(repr(addr) + ': could not connect')
			return

		try:
			# receive and send until closed
			while True:
				msg = obj_secure.receive()
				if not msg:
					print(repr(addr) + ': connection closed')
					break
				print(repr(addr) + ': ' + msg)
				new_msg = 'server response... ' + msg
				obj_secure.send(new_msg)
		except:
			print(repr(addr) + ': connection broke')
			return




HOST = '127.0.0.1'
PORT = 65432

f = open('./Connection/log_conn_server.txt', 'a')

server = ThreadedServer(HOST, PORT)
server.listen()
