from Connection.ConnInterface import ConnInterface
from Connection.ConnSocket import ConnSocketClient, ConnSocketServer
from Encryption import AESCipher, RSACipher


"""
============== Class Secure =============
global Implementations:
    disconnect()
    send()
    receive()
"""
class ConnSecure(ConnInterface):
    P = {
        'hello_msg': b'Hello Server',
        'secure_established': 'aes_is_set',
        'request_close_conn': 'request_close_secure_connection',
        'accept_close_conn': 'accept_close_secure_connection'
    }

    def __init__(self, base_conn, log_file):
        ConnInterface.__init__(self, log_file)
        self.s = base_conn
        if (type(base_conn) == ConnSocketClient) or (type(base_conn) == ConnSocketServer):
            self.type = 'secure_socket'
        else:
            self.type = 'secure_client'
        self.rsa = None
        self.aes = None

    def connect(self):
        raise NotImplementedError

    def disconnect(self):
        if not self.connected:
            return

        if self.s.connected:
            # send close request (should not fail)
            try:
                self.send(self.P["request_close_conn"], hard_fail=True)
            except Exception as e:
                self.log('Warning (disconnect): ' + repr(e))
            # disconnect base connection
            self.s.disconnect()
        # clear data
        self.aes = None
        self.rsa = None
        # set state to disconnected
        self.connected = False
        self.log('Success (disconnect)')

    def send(self, msg, hard_fail=False):
        if not self.connected or not self.s.connected:
            self.log('Error (send): not connected')
            raise ConnectionError('not connected')
        try:
            enc = self.aes.encrypt(msg)
            self.s.send(enc)
        except Exception as e:
            if not hard_fail:
                self.disconnect()
            self.log('Error (send): ' + repr(e))
            raise e

    def receive(self):
        if not self.connected or not self.s.connected:
            self.log('Error (receive): not connected')
            raise ConnectionError('not connected')

        try:
            data = self.s.receive()

            # case lower connection ended
            if not data:
                raise ConnectionError('base connection ended unexpectedly')

            # case while (BLOCKED) connection ended
            if not self.connected:
                self.log('State (receive): connection already closed')
                return None

            dec = self.aes.decrypt(data)

        except Exception as e:
            self.disconnect()
            self.log('Error (receive): ' + repr(e))
            raise e

        # received close connection request
        if dec == self.P['request_close_conn']:
            self.disconnect()
            self.log('State (receive): connection ended by host')
            return None

        return dec


"""
============== Client Secure =============
connect to server securely
must call connect()
"""
class ConnSecureClient(ConnSecure):
    def connect(self):
        if self.connected:
            self.log('Warning (connect): already connected')
            return True

        # set lower connection
        if not self.s.connect():
            return False

        try:
            # set encryption setup
            self.rsa = RSACipher.RSAPublic()
            self.aes = AESCipher.AESCipher()
            self.aes.gen_key()

            # set secure conn (raise an error if fails)
            self.open_secure_connection()
        except Exception as e:
            self.log("Error (connect): can't connect - " + repr(e))
            self.disconnect()
            return False

        self.connected = True
        return True

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
            raise e


"""
============== Server Secure =============
connect to client securely
base connection must be established before creating ConnSecureServer instance
must call connect()
"""
class ConnSecureServer(ConnSecure):
    def connect(self):
        if self.connected:
            self.log('Warning (connect): already connected')
            return True

        # check lower connection
        if not self.s.connected:
            self.log('Error (connect): lower is not connected')
            return False

        try:
            # set encryption setup
            self.rsa = RSACipher.RSAPrivate()
            self.aes = AESCipher.AESCipher()

            # set secure conn (raise an error if fails)
            self.open_secure_connection()
        except Exception as e:
            self.log("Error (connect): can't connect - " + repr(e))
            self.disconnect()
            return False

        self.connected = True
        return True

    def open_secure_connection(self):
        try:
            # receive hello msg
            data = self.s.receive()
            if not data:
                raise ConnectionError('base connection ended unexpectedly')
            if data != self.P['hello_msg']:
                raise ConnectionError('first connection protocol message not fit')

            # send RSA public key
            self.s.send(self.rsa.export_public())

            # receive encrypted symmetric key
            data = self.s.receive()
            if not data:
                raise ConnectionError('base connection ended unexpectedly')
            key = self.rsa.decrypt(data)
            self.aes.set_key(key)

            # send 'conn established' encrypted message
            enc = self.aes.encrypt(self.P['secure_established'])
            self.s.send(enc)

        except Exception as e:
            self.disconnect()
            self.log('Error (open_secure_connection): ' + repr(e))
            raise e
