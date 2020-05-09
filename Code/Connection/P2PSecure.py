from Encryption import RSAPublic, AESCipher, RSAPrivate


class P2PSecure:
	SERVER_PRE = b'dh3hd%dsjw'
	# state
	IDLE = 0
	KEY_EXT = 1
	SECURE = 2

	def __init__(self, username, p2p):
		self.username = username
		self.state = self.IDLE
		self.messages = []
		self.rsa = None
		self.aes = AESCipher()
		self.aes.gen_key()
		self.otheruser = None
		self.p2p = p2p
		self.old_msg = None

	def encrypt(self, data):
		return self.aes.encrypt(data)

	def get(self, msg):
		if self.state == self.SECURE:
			msg.data = self.aes.decrypt(msg.data)
			self.messages.append(msg)
			return

		if msg.data[:len(self.SERVER_PRE)] == self.SERVER_PRE:
			self.client_protocol(msg)
		else:
			self.server_protocol(msg)



	def add(self, msg):
		self.messages.append(msg)

	def server_protocol(self, msg):
		if self.state == self.IDLE:
			self.old_msg = msg
			self.otheruser = msg.from_
			self.rsa = RSAPrivate()
			self.aes = AESCipher()

			new_msg = b''.join([self.SERVER_PRE, self.rsa.export_public()])
			self.p2p.row_send(new_msg, self.otheruser)
			self.state = self.KEY_EXT

		elif self.state == self.KEY_EXT:
			key = self.rsa.decrypt(msg.data)
			self.aes.set_key(key)
			self.state = self.SECURE

			# first process older message (receive when connection wasn't established)
			tmp_msg = self.old_msg
			self.old_msg = None
			self.get(tmp_msg)

	def client_protocol(self, msg):
		if self.state == self.IDLE:
			self.otheruser = msg.from_
			self.rsa = RSAPublic()

			self.rsa.load_key(msg.data[len(self.SERVER_PRE):])
			encrypted = self.rsa.encrypt(self.aes.key)

			self.p2p.row_send(encrypted, self.otheruser)
			self.state = self.SECURE



