import socket
from time import sleep
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import RSACipher
import AESCipher
from enum import Enum
import threading
import datetime
import atexit

class Stat(Enum):
	HELLO = 1
	GET_KEY = 2
	SECURE = 3


class Client:
	HOST = '127.0.0.1'
	PORT = 65432
	PACK_SIZE = 1024
	MAX_RETRY = 3
	FORCE_CONNECTION = False
	LOG_FILE_PATH = 'log.txt'

	P = {
		'hello_msg': b'Hello Server',
		'secure_established': 'aes_is_set',
		'request_close_conn': 'request_close_secure_connection',
		'accept_close_conn': 'accept_close_secure_connection'
	}

	rsa = None
	aes = None
	connected = False
	s = None
	rx = None
	msg_drop_buff = []

	def __init__(self, rx_callback):
		self.rx_callback = rx_callback
		self.log = open(self.LOG_FILE_PATH, 'a')
		self.log.write('----------------------------------------\n')
		self.log.write(str(datetime.datetime.now()) + '\n')
		self.log.write('----------------------------------------\n')
		atexit.register(self.on_terminate)

	def connect(self):

		self.rsa = RSACipher.RSAPublic()
		self.aes = AESCipher.AESCipher()
		self.aes.gen_key()

		# socket connection
		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			self.s.connect((self.HOST, self.PORT))
		except:
			self.log.write("Fail (connect): can't connect socket\n")
			self.disconnect()
			return False

		# protocol connection
		if self.open_secure_connection():
			self.log.write('Success (connect): Secure Connection\n')
		else:
			self.log.write('Fail (connect): Secure Connection\n')
			self.disconnect()
			return False

		self.connected = True
		self.run_receive()

		# send not sent messages
		for i, msg in enumerate(self.msg_drop_buff):
			del self.msg_drop_buff[i]
			self.send(msg)

		return True

	def disconnect(self):
		self.send(self.P['request_close_conn'])
		for i in range(self.MAX_RETRY):
			if not self.connected:
				self.log.write('Success (disconnect): secure connection closed\n')
				return True
			sleep(1)
		self.clear_connection()
		self.log.write("Fail (disconnect): can't close listening thread\n")
		return False

	def open_secure_connection(self):
		state = Stat.HELLO
		ind_retry = 0

		while True:

			if state == Stat.HELLO:
				self.s.sendall(self.P['hello_msg'])
				state = Stat.GET_KEY
				self.log.write('HELLO: success\n')

			elif state == Stat.GET_KEY:
				try:
					self.rsa.load_key(data)
					encrypted = self.rsa.encrypt(self.aes.key)
					self.s.sendall(encrypted)
					state = Stat.SECURE
					self.log.write('GET_KEY: success\n')

				except Exception as e:
					self.log.write('Fail (open_secure_connection): create secure connection!\n')
					print(e)
					return False

			elif state == Stat.SECURE:
				try:
					msg = self.aes.decrypt(data)
					if msg == self.P['secure_established']:
						return True
					else:
						return False
				except Exception as e:
					self.log.write('Fail (open_secure_connection): create secure connection!\n')
					print(e)
					return False

			data = self.s.recv(self.PACK_SIZE)

			if data == b'':
				self.log.write('Error: Socket Disconnected\n')
				return False

	def clear_connection(self):
		self.aes = None
		self.rsa = None
		self.s.close()
		self.s = None
		self.connected = False

	def send(self, msg):
		if not self.connected:
			self.log.write('Fail (send): not connected\n')
			return False

		enc = self.aes.encrypt(msg)
		try:
			self.s.sendall(enc)
			return True
		except:
			# recreate the socket and reconnect
			self.log.write(f'Socket: connection broke\n')
			self.msg_drop_buff.append(msg)
			self.clear_connection()
			if self.FORCE_CONNECTION:
				self.connect()
				return True
			else:
				return False

	# core receiver implementation
	def receive(self):
		if not self.connected:
			self.log.write('Fail (receive): not connected\n')
			return False

		data = self.s.recv(self.PACK_SIZE)
		if not data:
			return ''

		dec = self.aes.decrypt(data)
		return dec

	# start receiver thread
	def run_receive(self):
		if not self.connected:
			self.log.write('Fail (run_receive): not connected\n')
			return False
		self.rx = threading.Thread(target=self.receive_runtime)
		self.rx.start()

	# receiver thread function
	def receive_runtime(self):
		while True:

			msg = self.receive()

			if msg == self.P['accept_close_conn']:
				self.connected = False
				self.clear_connection()
				self.log.write('Success (receive_runtime): Connection Closed By User\n')
				break
			elif msg == self.P['request_close_conn']:
				self.send(self.P['accept_close_conn'])
				self.connected = False
				self.clear_connection()
				self.log.write('Success (receive_runtime): Connection Closed By Server\n')
				break

			if msg:
				self.rx_callback(msg)
			else:
				self.log.write('Fail (receive_runtime): socket connection ended\n')
				self.connected = False
				self.disconnect()
				if self.FORCE_CONNECTION:
					self.connect()
				break

	def on_terminate(self):
		self.log.write('exit program\n')
		self.log.close()


def to_print(msg):
	print(msg)

client = Client(to_print)
client.connect()

while True:
	msg = input('Write Message Q[quit]: ')
	if msg == 'Q':
		client.disconnect()
		break
	# try reconnect
	if not client.send(msg):
		while True:
			sleep(1)
			print('No Connection... try again')
			if client.connect():
				break
