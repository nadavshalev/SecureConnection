import socket
from time import sleep
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import RSACipher
import AESCipher
from enum import Enum


class Stat(Enum):
	HELLO = 1
	GET_KEY = 2
	SECURE = 3


class Client:
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

		# crypto init
		self.rsa = RSACipher.RSAPublic()
		self.aes = AESCipher.AESCipher()
		self.aes.gen_key()

		# init socket
		self.s = None
		self.connect()

		# establish secure connection with server
		if self.open_secure_connection():
			print('Connection Established Successfully')
		else:
			raise RuntimeError('Fail To Establish Connection')

	def open_secure_connection(self):
		state = Stat.HELLO
		ind_retry = 0

		while True:
			# fail MAX_RETRY times
			if ind_retry == self.MAX_RETRY:
				return False

			if state == Stat.HELLO:
				self.s.sendall(self.P['hello_msg'])
				state = Stat.GET_KEY
				print('HELLO: success')

			elif state == Stat.GET_KEY:
				try:
					self.rsa.load_key(data)
					encrypted = self.rsa.encrypt(self.aes.key)
					self.s.sendall(encrypted)
					state = Stat.SECURE
					print('GET_KEY: success')

				except Exception as e:
					print('Connection Broke!')
					print(e)
					state = Stat.HELLO

			elif state == Stat.SECURE:
				try:
					msg = self.aes.decrypt(data)
					if msg == self.P['secure_established']:
						return True
					else:
						return False
				except Exception as e:
					print('Connection Broke!')
					print(e)
					state = Stat.HELLO

			data = self.s.recv(self.PACK_SIZE)
			if data == b'':
				print('Error: Socket Disconnected')
				return False

	def close_secure_connection(self):
		for i in range(3):
			self.send(self.P['request_close_conn'])
			if self.receive() == self.P['accept_close_conn']:
				self.aes = None
				self.rsa = None
				self.disconnect()
				print('Secure connection closed')
				return True
		raise RuntimeError('Fail to close secure connection')

	def send(self, msg):
		enc = self.aes.encrypt(msg)
		self.s.sendall(enc)

	def receive(self):
		data = self.s.recv(self.PACK_SIZE)
		if data == b'':
			raise RuntimeError('Connection Broke!')

		dec = self.aes.decrypt(data)

		# case server ask to close secure connection
		if dec == self.P['request_close_conn']:
			self.send(self.P['accept_close_conn'])
			self.aes = None
			self.rsa = None
			self.disconnect()
			print('Connection Closed By Server')
		return self.aes.decrypt(data)

	def connect(self):
		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.s.connect((self.HOST, self.PORT))

	def disconnect(self):
		self.s.close()


client = Client()
while True:
	msg = input('Write Message Q[quit]: ')
	if msg == 'Q':
		client.close_secure_connection()
		break
	client.send(msg)
	print(client.receive())
