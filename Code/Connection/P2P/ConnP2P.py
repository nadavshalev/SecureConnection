import datetime
import base64

from Connection import ConnInterface
import json

class ConnP2P:

    REQUEST_CLOSE_CONNECTION = b'request_close_connection_to_address'
    ADDR_SIZE = 32

    def __init__(self, base_conn, username, log_file):
        self.log_file = log_file
        self.connected = False
        self.s = base_conn
        self.type = 'p2p'
        self.username = username

    def disconnect(self):
        raise NotImplementedError

    def send_(self, msg: bytes, hard_fail=False):
        if not self.connected or not self.s.connected:
            self.log('Error (send): not connected')
            raise ConnectionError('not connected')
        try:

            self.s.send(msg)

        except Exception as e:
            if not hard_fail:
                self.disconnect()
            self.log('Error (send): ' + repr(e))
            raise e

    def receive(self) -> bytes:
        if not self.connected or not self.s.connected:
            self.log('Error (receive): not connected')
            raise ConnectionError('not connected')

        try:
            data = self.s.receive()
            if not data:
                if self.connected:
                    raise ConnectionError('base connection ended unexpectedly')
                else:
                    self.log('State (receive): connection already closed')
                    return b''

        except Exception as e:
            self.disconnect()
            self.log('Error (receive): ' + repr(e))
            raise e

        return data

    def encode(self, msg: bytes, to_: str, from_: str) -> bytes:
        if not to_:
            to_ = ''
        if not from_:
            from_ = ''
        fmat = "{:<" + str(self.ADDR_SIZE) + "}"
        bto_ = fmat.format(to_).encode()
        bfrom_ = fmat.format(from_).encode()
        return bto_ + bfrom_ + msg

    def decode(self, data: bytes):
        to_ = data[:self.ADDR_SIZE].decode().strip()
        from_ = data[self.ADDR_SIZE:2*self.ADDR_SIZE].decode().strip()
        msg = data[2*self.ADDR_SIZE:]
        if not to_:
            to_ = None
        if not from_:
            from_ = None
        return msg, to_, from_

    def get_addr(self):
        return self.username

    def log(self, msg):
        self.log_file.write(str(datetime.datetime.now()) + '\t' + repr(self.get_addr()) + '\t\t\t\t\t' + self.type + ':\t\t' + msg + '\n')
