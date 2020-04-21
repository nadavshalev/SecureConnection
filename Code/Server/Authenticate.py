import hashlib
import json
import secrets

from Code.Server.DBusers import User, Users

class Authentication:
	SERVER_KEY_LEN = 32

	def __init__(self, users_db):
		self.users_db = users_db

	def auth_get(self, data):
		addr, password, action = self.unpack(data)
		hash_pass = self.set_hash(password)

		if action == 'validate':
			return self.users_db.validate_user(addr, hash_pass)
		else:
			key = secrets.token_urlsafe(self.SERVER_KEY_LEN)
			server_hash = self.set_hash(key)
			user = User(addr, hash_pass, server_hash)
			return self.users_db.insert_user(user)

	def pack(self, addr, password, action):
		data = {
			"addr": addr,
			"pass": password,
			"action": action
		}
		return json.dumps(data)

	def unpack(self, data):
		msg = json.loads(data)
		return msg["addr"], msg["pass"], msg["action"]

	def set_hash(self, str_data):
		return hashlib.sha256(str_data.encode()).digest()

# users = Users()
#
# auth = Authentication(users)
#
# data = auth.pack('nadav', '123123', 'create')
# print(auth.auth_get(data))
# data = auth.pack('shani', 'asdasd', 'create')
# print(auth.auth_get(data))
#
#
# data = auth.pack('nadav', '123123', 'validate')
# print(auth.auth_get(data))
# data = auth.pack('nadav', '123124', 'validate')
# print(auth.auth_get(data))
#
#
# data = auth.pack('shani', 'qweqwe', 'create')
# print(auth.auth_get(data))

