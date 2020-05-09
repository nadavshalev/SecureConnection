from Connection.P2P import P2PMessage
from Encryption import RSAPublic, AESCipher, RSAPrivate


class P2PSecure:
	"""
	Set P2P encrypted connection.
	Use P2PClient to connect unsecured with encrypted messages.
	The Class is user+target specific (one p2p conn only)
	"""

	SERVER_PRE = b'dh3hd%dsjw'  # pseudo random string to recognize server public key

	# state
	IDLE = 0
	KEY_EXT = 1
	SECURE = 2

	# conn type
	TYPE_CLIENT = True
	TYPE_SERVER = False

	def __init__(self, username, p2p):
		self.username = username  # my username
		self.state = self.IDLE  # connection state - not secure
		self.messages = []  # message buffer
		self.rsa = None  # RSA obj place

		# AES - init and gen key in case send before secure the connection
		self.aes = AESCipher()
		self.aes.gen_key()

		self.otheruser = None  # other user address. filled while secure the connection
		self.p2p = p2p  # p2p object
		self.old_msg = None  # old message buffer - case got message before secure the connection
		self.type = None

	def encrypt(self, data: bytes) -> bytes:
		"""
		:param data: data to encrypt
		:return: encrypted message
		"""
		return self.aes.encrypt(data)

	def get(self, msg: P2PMessage):
		"""
		Decode the received message, and set the secure connection if needed
		Called by p2p.listen() function each time receive message for this user+target pair
		:param msg: P2PMessage object with to_ = self.username, from_ = self.otheruser
		"""

		# case connection already secure - just decrypt
		if self.state == self.SECURE:
			msg.data = self.aes.decrypt(msg.data)
			self.messages.append(msg)
			return

		# not secured yet
		# get connection type:
		# 	server - received encrypted message
		# 	client - received public key from server with SERVER_PRE init
		if not self.type:
			if msg.data[:len(self.SERVER_PRE)] == self.SERVER_PRE:
				self.type = self.TYPE_CLIENT
			else:
				self.type = self.TYPE_SERVER

		# handle connection according to the type
		if self.type == self.TYPE_CLIENT:
			self.client_protocol(msg)
		else:
			self.server_protocol(msg)

	def add(self, msg: P2PMessage):
		"""
		Insert new (not encrypted) messages to object.
		:param msg: unencrypted message
		"""
		self.messages.append(msg)

	def server_protocol(self, msg: P2PMessage):
		"""
		Handle server-side secure protocol
		:param msg: received message
		"""

		# nothing so far
		if self.state == self.IDLE:
			self.old_msg = msg  # save encrypted message for later decryption
			self.otheruser = msg.from_  # get other-user name

			# init encryption objects
			self.rsa = RSAPrivate()
			self.aes = AESCipher()

			# create public key message
			new_msg = b''.join([self.SERVER_PRE, self.rsa.export_public()])
			# send using p2p obj without encryption
			self.p2p.row_send(new_msg, self.otheruser)
			self.state = self.KEY_EXT  # update state

		# now decode symmetric key from RSA encryption
		elif self.state == self.KEY_EXT:
			# decode and update key
			key = self.rsa.decrypt(msg.data)
			self.aes.set_key(key)
			self.state = self.SECURE

			# first process older message (receive when connection wasn't established)
			tmp_msg = self.old_msg
			self.old_msg = None
			self.get(tmp_msg)

	def client_protocol(self, msg: P2PMessage):
		"""
		Handle server-side secure protocol
		:param msg: received message
		"""

		# nothing so far
		if self.state == self.IDLE:
			self.otheruser = msg.from_   # get other-user name
			self.rsa = RSAPublic()

			# encrypt symmetric key using server's RSA public key
			self.rsa.load_key(msg.data[len(self.SERVER_PRE):])
			encrypted = self.rsa.encrypt(self.aes.key)

			# send to server
			self.p2p.row_send(encrypted, self.otheruser)
			self.state = self.SECURE



