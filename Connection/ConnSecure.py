from Connection.ConnInterface import ConnInterface
from Connection.ConnSocket import ConnSocket
from Encryption import AESCipher, RSACipher


class ConnSecure(ConnInterface):

    rsa = None
    aes = None
    P = {
        'hello_msg': b'Hello Server',
        'secure_established': 'aes_is_set',
        'request_close_conn': 'request_close_secure_connection',
        'accept_close_conn': 'accept_close_secure_connection'
    }

    def __init__(self, base_conn, log_file):
        ConnInterface.__init__(self, log_file)
        self.s = base_conn
        if type(base_conn) == ConnSocket:
            self.type = 'secure_server'
        else:
            self.type = 'secure'

    def connect(self):
        # set lower connection
        if not self.s.connect():
            return False

        # set encryption setup
        self.rsa = RSACipher.RSAPublic()
        self.aes = AESCipher.AESCipher()
        self.aes.gen_key()

        # set secure conn (raise an error if fails)
        self.open_secure_connection()

        self.connected = True
        return True

    def disconnect(self):
        # send close request (should not fail)
        try:
            self.send(self.P["request_close_conn"], hard_fail=True)
        except:
            pass
        # disconnect base connection
        self.s.disconnect()
        # clear data
        self.aes = None
        self.rsa = None
        # set state to disconnected
        self.connected = False

    def send(self, msg, hard_fail=False):
        if not self.connected:
            self.log('Error (send): not connected')
            raise ConnectionError('not connected')
        try:
            enc = self.aes.encrypt(msg)
            self.s.send(enc)
        except Exception as e:
            if not hard_fail:
                self.disconnect()
            self.log('Error (send): ' + repr(e))
            raise ConnectionError(str(e))

    def receive(self):
        if not self.connected:
            self.log('Error (receive): not connected')
            raise ConnectionError('not connected')

        try:
            data = self.s.receive()
            if not data:
                raise ConnectionError('base connection ended unexpectedly')
            dec = self.aes.decrypt(data)
        except Exception as e:
            self.disconnect()
            self.log('Error (receive): ' + repr(e))
            raise ConnectionError(str(e))

        if dec == self.P['request_close_conn']:
            self.disconnect()
            self.log('State (receive): connection ended by host')
            return None

        return dec

    def open_secure_connection(self):

        try:
            self.s.send(self.P['hello_msg'])

            data = self.s.receive()
            if not data:
                raise ConnectionError('base connection ended unexpectedly')

            self.rsa.load_key(data)
            encrypted = self.rsa.encrypt(self.aes.key)
            self.s.send(encrypted)

            data = self.s.receive()
            if not data:
                raise ConnectionError('base connection ended unexpectedly')

            msg = self.aes.decrypt(data)
            if msg != self.P['secure_established']:
                raise ConnectionError('decrypted message not fit')

        except Exception as e:
            self.disconnect()
            self.log('Error (open_secure_connection): ' + repr(e))
            raise ConnectionError(str(e))



f = open('log_conn.txt', 'a')
conn_socket = ConnSocket('127.0.0.1', 65432, f)
conn_secure = ConnSecure(conn_socket, f)
conn_secure.connect()
while True:
    msg = input('Write Message Q[quit]: ')
    if msg == 'Q':
        conn_secure.disconnect()
        break
    conn_secure.send(msg)
    print(conn_secure.receive())


y = input('q: ')
x = float(y)
if y == 'yes':
    pass