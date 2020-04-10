import socket
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import binascii
import RSACipher
import AESCipher
from enum import Enum
from time import sleep
import types


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

		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.s.bind((self.HOST, self.PORT))
		self.s.listen()


	def start(self):
		# get connections forever
		while True:
			session = types.SimpleNamespace()

			session.conn, session.addr = self.s.accept()
			print('Connected by', session.addr)

			session.rsa = RSACipher.RSAPrivate()
			session.aes = AESCipher.AESCipher()

			if not self.open_secure_connection(session):
				self.disconnect(session)
				continue

			# read and response forever
			while True:
				msg = self.receive(session)
				if msg is None:
					self.disconnect(session)
					break
				new_msg = 'server response... ' + msg
				print(new_msg)
				self.send(session, new_msg)

	def open_secure_connection(self, session):
		state = Stat.HELLO

		while True:

			data = session.conn.recv(1024)

			# case socket closed by client
			if data == b'':
				print('Error: Socket Disconnected')
				return False

			if state == Stat.HELLO:
				if data == self.P['hello_msg']:
					session.conn.sendall(self.export_rsa_key(session))
					state = Stat.GET_KEY
					print('HELLO: success')
				else:
					return False

			elif state == Stat.GET_KEY:
				try:
					key = session.rsa.decrypt(data)
					session.aes.set_key(key)
					enc = session.aes.encrypt(self.P['secure_established'])
					session.conn.sendall(enc)
					state = Stat.SECURE
					print('GET_KEY: success')
					return True
				except Exception as e:
					print('Connection Reset...')
					print(e)
					return False

	def close_secure_connection(self, session):
		self.send(session, self.P['request_close_conn'])
		self.disconnect(session)
		print('Secure connection closed')

	def send(self, session, msg):
		enc = session.aes.encrypt(msg)
		session.conn.sendall(enc)

	def receive(self, session):
		data = session.conn.recv(self.PACK_SIZE)
		if data == b'':
			print('Connection Broke!')
			return None

		dec = session.aes.decrypt(data)

		# case server ask to close secure connection
		if dec == self.P['request_close_conn']:
			self.send(session, self.P['accept_close_conn'])
			print('Connection Closed By User')
			return None
		return session.aes.decrypt(data)

	def disconnect(self, session):
		session.aes = None
		session.rsa = None
		session.conn.close()

	def export_rsa_key(self, session):
		return session.rsa.export_public()


server = Server()
server.start()