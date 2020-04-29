import threading

from Connection import ConnSocketClient, ConnSecureClient, ConnP2PClient, ConnSecureClientAccept, ConnSecureServer


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
		self.listen_conn = None
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
		conn = self.init_create_connection()
		if not conn or not conn.connect():
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
		threading.Thread(target=self.init_accept_callback, args=(callback,)).start()

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

		msg_bytes = self.conn.receive()
		if not msg_bytes:
			return None
		return msg_bytes.decode()

	def receive_callback(self, callback):
		"""
		Set callback function to handle the received messages without blocking
		:param callback: function. prarm1: ClientObj, param2: message
		"""
		threading.Thread(target=self.init_receive_callback, args=(callback,)).start()

	def disconnect(self):
		if self.conn:
			self.conn.disconnect()
			self.target_address = None
		if self.listen_conn:
			self.listen_conn.destroy()

	def init_create_connection(self):
		conn_socket = ConnSocketClient(self.IP, self.PORT, self.logfile)
		conn_secure = ConnSecureClient(conn_socket, self.logfile)
		conn_p2p = ConnP2PClient(conn_secure, self.address, self.logfile)

		if conn_p2p.connect():
			return ConnSecureServer(conn_p2p, self.logfile)
		else:
			return None

	def init_accept_callback(self, callback):
		while True:
			self.listen_conn = self.init_create_connection()
			if self.listen_conn.connect():
				# create new client for connection
				new_client = Client(self.address, self.password, self.log_file_name)
				new_client.conn = self.listen_conn
				new_client.target_address = self.listen_conn.s.conn_addr

				# start callback thread
				threading.Thread(target=callback, args=(new_client,)).start()

	def init_receive_callback(self, callback):
		while True:
			if not self.conn:
				break
			msg = self.receive()
			callback(self, msg)
			if not msg:
				break
