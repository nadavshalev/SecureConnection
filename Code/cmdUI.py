import time

import os

from Client import Client

from pynput.keyboard import Key, Listener

class cmdUI:

	UPDATE_TIME = 1

	def __init__(self):
		self.my_addr = None
		self.conns = {}
		self.key_listener = Listener(on_press=self.on_press)
		self.from_keyboard = None
		self.key_buff = ''

	def run(self):
		self.my_addr = input('Name:')

		client = Client(self.my_addr, 'dummy password')

		client.accept_callback(self.update_cunnections)

		self.menu_layout()

	def menu_layout(self):
		self.key_listener.start()
		while self.from_keyboard != 'q':
			self.clear_screen()
			print(self.from_keyboard)
			print(self.key_buff)
			for i, name in enumerate(self.conns):
				print(f'{i}:\t{name}\t{self.conns[name]["unread"]}')
				if self.from_keyboard == i:
					print(f'move to conversation number {i}, {name}')
					time.sleep(5)
			self.from_keyboard = None
			time.sleep(self.UPDATE_TIME)
		self.do_exit()

	def update_cunnections(self, conn):
		conn_dict = {
			'conn': conn,
			'addr': conn.target_address,
			'msg': [],
			'unread': 0
		}
		self.conns[conn.target_address] = conn_dict
		conn.receive_callback(self.update_receive)

	def update_receive(self, conn, msg):
		if msg:
			msg_dict = {
				'from': conn.target_address,
				'data': msg
			}
			conn_dict = self.conns[conn.target_address]
			conn_dict['msg'] = msg_dict
			conn_dict['unread'] += 1
		else:
			del self.conns[conn.target_address]

	@staticmethod
	def clear_screen():

		# for windows
		if os.name == 'nt':
			_ = os.system('cls')

		# for mac and linux(here, os.name is 'posix')
		else:
			_ = os.system('clear')

	def on_press(self, key):

		if key == Key.enter:
			print(self.key_buff)
			if self.key_buff:
				try:
					num = int(self.key_buff)
					if len(self.conns) > num:
						self.from_keyboard = num
				except:
					pass
			self.key_buff = ''

		else:
			try:
				if key.char == 'q':
					self.from_keyboard = 'q'
					return

				self.key_buff += key.char
			except:
				self.key_buff = ''

	def do_exit(self):
		for conn in self.conns:
			conn.disconnect()
		if self.key_listener.is_alive():
			self.key_listener.stop()
		print('exit UI')


c = cmdUI()
c.run()
