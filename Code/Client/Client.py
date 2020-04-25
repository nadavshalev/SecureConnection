import threading

from Connection import ConnSocketClient, ConnSecureClient, ConnP2PClient, ConnSecureClientAccept


class Client:
	PORT = 65432
	IP = '127.0.0.1'

	DEFAULT_LOG_FILE = 'clientLog.log'
	LOG_TYPE = 'a'

	def __init__(self, address, password, log_file_name=None):
		self.address = address
		self.password = password
		if not log_file_name:
			log_file_name = self.DEFAULT_LOG_FILE
		self.log_file_name = log_file_name
		self.logfile = open(log_file_name, self.LOG_TYPE)

		self.conn = None
		self.target_address = None

	def connect(self, to_address):
		"""
		Connect to other user by address.
		Failed if other user is not in accept mode
		:param to_address: address of a user
		:return: bool - True if success
		"""

		conn_socket = ConnSocketClient(self.IP, self.PORT, self.logfile)
		conn_secure = ConnSecureClient(conn_socket, self.logfile)
		conn_p2p = ConnP2PClient(conn_secure, self.address, self.logfile, to_address)

		client_secure = ConnSecureClient(conn_p2p, self.logfile)
		if not client_secure.connect():
			return False
		self.conn = client_secure
		self.target_address = to_address
		return True

	def accept(self):
		"""
		Wait for connection from other users.
		Block until connection established.
		:return: bool - True if success
		"""
		conn = self.accept_init()
		if not conn:
			return False
		self.conn = conn
		self.target_address = conn.s.conn_addr
		return True


	def accept_callback(self, callback):
		"""
		Wait for connection from other users.
		Not Blocking.
		When connection established - create a new thread and run the callback method
		:param callback:
		"""
		threading.Thread(target=self.accept_callback_init, args=(callback,)).start()

	def send(self, msg):
		"""
		:param msg: message to send
		:return: bool - True on success
		"""

		if not self.conn:
			return False
		self.conn.send(msg.encode())
		return True


	def receive(self):
		"""
		:return: received message or None if not connected
		"""

		if not self.conn:
			return None
		msg_bytes = self.conn.receive()
		if not msg_bytes:
			return None
		return msg_bytes.decode()

	def receive_callback(self, callback):
		"""
		Set callback function to handle the received messages without blocking
		:param callback: function. prarm1: ClientObj, param2: message
		"""
		threading.Thread(target=self.receive_callback_init, args=(callback,)).start()

	def disconnect(self):
		if self.conn:
			self.conn.disconnect()
			self.target_address = None

	def accept_init(self):
		conn_socket = ConnSocketClient(self.IP, self.PORT, self.logfile)
		conn_secure = ConnSecureClient(conn_socket, self.logfile)
		conn_p2p = ConnP2PClient(conn_secure, self.address, self.logfile)

		client_secure = ConnSecureClientAccept(conn_p2p, self.logfile)
		if not client_secure.connect():
			return None
		return client_secure

	def accept_callback_init(self, callback):
		while True:
			conn = self.accept_init()

			# create new client for connection
			new_client = Client(self.address, self.password, self.log_file_name)
			new_client.conn = conn
			new_client.target_address = conn.s.conn_addr

			# start callback thread
			threading.Thread(target=callback, args=(new_client,)).start()

	def receive_callback_init(self, callback):
		while True:
			msg = self.receive()
			if not msg:
				break
			callback(self, msg)
