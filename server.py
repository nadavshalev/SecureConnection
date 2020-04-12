import socket
from Encryption import AESCipher, RSACipher
from enum import Enum
import types


from Connection.ConnSecure import ConnSecureServer
from Connection.ConnSocket import ConnSocketServer

HOST = '127.0.0.1'
PORT = 65432

f = open('./Connection/log_conn_server.txt', 'a')

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen()

while True:
	conn, addr = s.accept()
	print('Connected by', addr)
	obj_sock = ConnSocketServer(conn, f)
	obj_secure = ConnSecureServer(obj_sock, f)

	if not obj_secure.connect():
		print('could not connect')
		break

	try:
		# receive and send until closed
		while True:
			msg = obj_secure.receive()
			if not msg:
				print('connection closed')
				break
			print(msg)
			new_msg = 'server response... ' + msg
			obj_secure.send(new_msg)
	except:
		print('connection broke')
		break