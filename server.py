import socket
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import binascii
import RSACipher
import AESCipher
from enum import Enum
from time import sleep


class Stat(Enum):
	HELLO = 1
	GET_KEY = 2
	SECURE = 3
	RESET = 4

class Server:
	HOST = '127.0.0.1'
	PORT = 65432
	PACK_SIZE = 1024
	MAX_RETRY = 3

	P = {
		'hello_msg': b'Hello Server',
		'secure_established': 'aes_is_set',
		'request_close_conn': 'request_close_secure_connection',
		'accept_close_conn': 'accept_close_secure_connection'
	}

	def __init__(self):
		self.rsa = RSACipher.RSAPrivate()
		self.aes = AESCipher.AESCipher()

		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.s.bind((self.HOST, self.PORT))
		self.s.listen()

	def start(self):
		while True:
			conn, addr = self.s.accept()
			print('Connected by', addr)

			self.open_secure_connection(conn)

			while True:
				msg = self.receive(conn)
				if msg is None:
					break
				new_msg = 'server response... ' + msg
				print(new_msg)
				self.send(conn, new_msg)

			# self.close_secure_connection(conn)
			# break

	def open_secure_connection(self, conn):
		state = Stat.HELLO
		ind_retry = 0

		while True:
			# fail MAX_RETRY times
			if ind_retry == self.MAX_RETRY:
				return False

			data = conn.recv(1024)

			# case socket closed by client
			if data == b'':
				print('Error: Socket Disconnected')
				return False

			if state == Stat.HELLO:
				if data == self.P['hello_msg']:
					conn.sendall(self.export_rsa_key())
					state = Stat.GET_KEY
					print('HELLO: success')

			elif state == Stat.GET_KEY:
				try:
					key = self.rsa.decrypt(data)
					self.aes.set_key(key)
					enc = self.aes.encrypt(self.P['secure_established'])
					conn.sendall(enc)
					state = Stat.SECURE
					print('GET_KEY: success')
					break
				except Exception as e:
					print('Connection Reset...')
					print(e)
					state = Stat.HELLO

	def close_secure_connection(self, conn):
		for i in range(3):
			self.send(conn, self.P['request_close_conn'])
			if self.receive(conn) == self.P['accept_close_conn']:
				self.aes = None
				self.rsa = None
				self.disconnect(conn)
				print('Secure connection closed')
				return True
		raise RuntimeError('Fail to close secure connection')

	def send(self, conn, msg):
		enc = self.aes.encrypt(msg)
		conn.sendall(enc)

	def receive(self, conn):
		data = conn.recv(self.PACK_SIZE)
		if data == b'':
			raise RuntimeError('Connection Broke!')

		dec = self.aes.decrypt(data)

		# case server ask to close secure connection
		if dec == self.P['request_close_conn']:
			self.send(conn, self.P['accept_close_conn'])
			self.aes = None
			self.rsa = None
			self.disconnect(conn)
			print('Connection Closed By User')
			return None
		return self.aes.decrypt(data)

	def disconnect(self, conn):
		conn.close()

	def export_rsa_key(self):
		return self.rsa.export_public()


server = Server()
server.start()