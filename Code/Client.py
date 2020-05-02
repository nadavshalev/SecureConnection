import queue
import threading

from Connection import ConnSocketClient, ConnSecureClient, ConnP2PClient, ConnSecureClientAccept, ConnSecureServer
from Connection.P2P import P2PMessage


class Client:
	PORT = 65432
	IP = '127.0.0.1'

	DEFAULT_LOG_FILE = 'clientLog.log'
	LOG_TYPE = 'a'

	def __init__(self, username, password, log_file_name=None):
		self.username = username
		self.password = password
		if not log_file_name:
			log_file_name = self.DEFAULT_LOG_FILE
		self.log_file_name = log_file_name
		self.logfile = open(log_file_name, self.LOG_TYPE)

		self.connected = False
		self.conn = None
		self.conn_dict = {}

	def connect(self):

		conn_socket = ConnSocketClient(self.IP, self.PORT, self.logfile)
		conn_secure = ConnSecureClient(conn_socket, self.logfile)
		conn_p2p = ConnP2PClient(conn_secure, self.username, self.conn_dict, self.logfile)
		if not conn_p2p.connect():
			return False
		self.conn = conn_p2p
		self.conn.listen()
		self.connected = True
		return True

	def send(self, data, to_address):
		"""
		:param msg: message to send
		:return: bool - True on success
		"""

		if not self.conn:
			return False

		try:
			self.conn.send(data.encode(), to_address)
		except:
			return False

		if to_address not in self.conn_dict:
			self.conn_dict[to_address] = queue.Queue()
		msg = P2PMessage(data.encode(), to_address, self.username)
		self.conn_dict[to_address].put(msg)
		return True

	def disconnect(self):
		if self.conn:
			self.conn.disconnect()
		self.connected = False

	def print_status(self):
		for user in self.conn_dict:
			print(user)
			for msg in self.conn_dict[user].queue:
				if msg.from_ == self.username:
					print('\tme:\t' + msg.data.decode())
				else:
					print(f'\t{user}:\t' + msg.data.decode())
