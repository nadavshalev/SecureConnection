import socket
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import binascii
import RSACipher
import AESCipher
from enum import Enum


class Stat(Enum):
	HELLO = 1
	GET_KEY = 2
	SECURE = 3
	RESET = 4


P = {
	'hello_msg': b'Hello Server',
	'secure_established': 'aes_is_set',
	'request_close_conn': 'request_close_secure_connection',
	'accept_close_conn': 'accept_close_secure_connection'
}


HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 65432        # Port to listen on (non-privileged ports are > 1023)

rsa = RSACipher.RSAPrivate()
pub_key = rsa.export_public()

aes = AESCipher.AESCipher()

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
	s.bind((HOST, PORT))
	s.listen()

	state = Stat.HELLO
	while True:


		conn, addr = s.accept()

		# with conn:
		print('Connected by', addr)

		while True:
			print()
			data = conn.recv(1024)
			print(data)
			if data == b'':
				break

			if state == Stat.HELLO:
				if data == P['hello_msg']:
					conn.sendall(pub_key)
					state = Stat.GET_KEY
					print('HELLO: success')

			elif state == Stat.GET_KEY:
				try:
					key = rsa.decrypt(data)
					aes.set_key(key)
					enc = aes.encrypt(P['secure_established'])
					conn.sendall(enc)
					state = Stat.SECURE
					print('GET_KEY: success')
				except Exception as e:
					print('Connection Reset...')
					print(e)
					# state = Stat.HELLO

			elif state == Stat.SECURE:
				try:
					msg = aes.decrypt(data)
					if msg == P['request_close_conn']:
						new_msg = P['accept_close_conn']
						enc = aes.encrypt(new_msg)
						conn.sendall(enc)
						print('connection closed')
						break
					else:
						print(msg)
						new_msg = 'server response... ' + msg
						enc = aes.encrypt(new_msg)
						conn.sendall(enc)
				except Exception as e:
					print('Connection Reset...')
					print(e)
					# state = Stat.HELLO
