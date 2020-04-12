import socket
from Connection.ConnSecure import ConnSecureServer
from Connection.ConnSocket import ConnSocketServer
import socket
import threading
import json


class ThreadedServer:
	def __init__(self, host, port):
		self.host = host
		self.port = port
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.bind((self.host, self.port))
		self.conn_dict = dict()

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

		self.conn_dict[repr(addr)] = obj_secure

		if not obj_secure.connect():
			print(repr(addr) + ': could not connect')
			return

		try:
			# receive and send until closed
			while True:
				msg_str = obj_secure.receive()
				if not msg_str:
					print(repr(addr) + ': connection closed')
					break

				msg = json.loads(msg_str)
				print(f'from: {repr(addr)}\t to: {msg["to"]}\t data: {msg["msg"]}')

				self.conn_dict[msg["to"]].send(msg["msg"])
				# obj_secure.send(msg["msg"])
		except Exception as e:
			print(repr(addr) + ': connection broke - ' + repr(e))
			return




HOST = '127.0.0.1'
PORT = 65432

f = open('./Connection/log_conn_server.txt', 'a')

server = ThreadedServer(HOST, PORT)
server.listen()
