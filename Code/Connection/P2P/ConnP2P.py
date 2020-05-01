import datetime
import base64

from Connection import ConnInterface
import json




class P2PMessage:
    DELIM = '!~!'

    def __init__(self, data: bytes, to_: str = '', from_: str = ''):
        self.data = data
        self.to_ = to_
        self.from_ = from_

    def validate(self):
        pass

    def encode(self) -> bytes:
        header = self.to_ + self.DELIM + self.from_ + self.DELIM
        msg = [header.encode(), self.data]
        return b''.join(msg)

    @staticmethod
    def decode(data: bytes):
        data_split = data.split(P2PMessage.DELIM.encode(), 2)
        if len(data_split) != 3:
            raise ValueError('cant split to 3')
        return P2PMessage(data_split[2], data_split[0].decode(), data_split[1].decode())


class ConnP2P(ConnInterface):

    P = {
        'request_new_connection': b'request_connection_to_address',
        'wait_for_connection': b'wait_for_connection_from_anyone',
        'accept_connection': b'accept_connection_to_address',
        'set_connection': b'set_connection_from_address',
        'request_close_connection': b'request_close_connection_to_address',
        'closed_connection': b'closed_connection_from_address',
        'closed_connection_accepted': b'closed_connection_accepted_by_user'
    }
    ADDR_SIZE = 32

    def __init__(self, base_conn, username, log_file):
        ConnInterface.__init__(self, log_file)
        self.s = base_conn
        self.type = 'p2p'
        self.username = username
        self.conn_addr = None

    def connect(self):
        raise NotImplementedError

    def disconnect(self):
        raise NotImplementedError

    def send(self, msg: bytes, hard_fail=False):
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
