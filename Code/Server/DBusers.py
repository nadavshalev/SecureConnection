import sqlite3
from sqlite3 import Error

class User():

	def __init__(self, addr, user_hash, server_hash):
		self.addr = addr
		self.user_hash = user_hash
		self.server_hash = server_hash

	def get_tuple(self):
		return self.addr, self.user_hash, self.server_hash

	def __repr__(self):
		return f'addr: {self.addr}, user_hash: {self.user_hash}, server_hash: {self.server_hash}'


class Users():
	DB_NAME = 'server_db.db'
	TABLE_NAME = 'users'

	def __init__(self):
		"""
		Set connection to the db.
		Create users table if not exits.
		Raise an error if cant connect.
		"""

		conn = sqlite3.connect(self.DB_NAME)
		self.conn = conn

		# check users table exits
		curs = conn.cursor()
		curs.execute('SELECT name from sqlite_master where type= "table"')
		table_exist = (self.TABLE_NAME,) in curs.fetchall()
		if not table_exist:
			self.create_users_table()

	def insert_user(self, user):
		"""
		Insert new user to db.
		:param user: User Object
		:return bool - True if success
		"""

		addr, user_hash, server_hash = user.get_tuple()
		curs = self.conn.cursor()
		try:
			curs.execute("INSERT INTO " + self.TABLE_NAME + " VALUES(?,?,?)", (addr, user_hash, server_hash))
			self.conn.commit()
			return True
		except:
			return False

	def get_user(self, addr):
		"""
		:param addr: address of selected user
		:return: User obj, None if not exist
		"""

		curs = self.conn.cursor()
		curs.execute('SELECT * FROM users WHERE addr=?', (addr,))
		rows = curs.fetchall()
		# if row not exits
		if len(rows) == 0:
			return None
		# addr is primary key => only 1 row
		return User(rows[0][0], rows[0][1], rows[0][2])

	def validate_user(self, addr, user_hash):
		"""
		check user hashed password
		:param addr: user addr to check for
		:param user_hash: user hashed password received
		:return: bool - True if hash are equal
		"""

		user = self.get_user(addr)
		if not user:
			return False
		return user.user_hash == user_hash

	def create_users_table(self):
		curs = self.conn.cursor()
		curs.execute("CREATE TABLE " + self.TABLE_NAME + "(\
							addr		text 	PRIMARY KEY,\
							user_hash 	text	NOT NULL,\
							server_hash	text	NOT NULL)")
		self.conn.commit()
