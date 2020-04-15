import datetime
import base64

from Connection.ConnInterface import ConnInterface
import json
import threading


class ConnP2P(ConnInterface):

    P = {
        'request_new_connection': 'request_connection_to_address',
        'wait_for_connection': 'wait_for_connection_from_anyone',
        'accept_connection': 'accept_connection_to_address',
        'set_connection': 'set_connection_from_address',
        'request_close_connection': 'request_close_connection_to_address',
        'closed_connection': 'closed_connection_from_address',
        'closed_connection_accepted': 'closed_connection_accepted_by_user'
    }

    def __init__(self, base_conn, my_addr, log_file):
        ConnInterface.__init__(self, log_file)
        self.s = base_conn
        self.type = 'p2p'
        self.my_addr = my_addr
        self.conn_addr = None

    def connect(self):
        raise NotImplementedError

    def disconnect(self):
        raise NotImplementedError

    def send(self, msg, hard_fail=False):
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

    def receive(self):
        if not self.connected or not self.s.connected:
            self.log('Error (receive): not connected')
            raise ConnectionError('not connected')

        try:
            data_str = self.s.receive()
            if not data_str:
                if self.connected:
                    raise ConnectionError('base connection ended unexpectedly')
                else:
                    self.log('State (receive): connection already closed')
                    return None, None, None

            # decode json
            data, to_addr, from_addr = self.decode(data_str)

        except Exception as e:
            self.disconnect()
            self.log('Error (receive): ' + repr(e))
            raise e

        return data, to_addr, from_addr

    def validate_receive(self, msg, to_, from_):

        # case 'my_name' is not the message address
        if self.my_addr != to_:
            self.log('Error (validate_receive): message received in wrong address')
            return False

        # case already connected to address
        if self.conn_addr and self.conn_addr != from_:
            self.log('Error (validate_receive): message sent from wrong address')
            return False

        return True

    def encode(self, msg, to_, from_):
        type_ = type(msg)
        if type_ == bytes:
            msg = base64.b64encode(msg).decode()
        d = {
            'data': msg,
            'addr': {
                'to': to_,
                'from': from_
            },
            'type': str(type_)
        }
        return json.dumps(d)

    def decode(self, data):
        print(data)
        msg = json.loads(data)
        addr = msg['addr']
        if msg['type'] == "<class 'bytes'>":
            msg_data = base64.b64decode(msg['data'].encode())
        else:
            msg_data = msg['data']
        to_ = addr['to']
        from_ = addr['from']
        return msg_data, to_, from_

    def get_addr(self):
        return self.my_addr

    def log(self, msg):
        self.log_file.write(str(datetime.datetime.now()) + '\t' + repr(self.get_addr()) + '\t\t\t' + self.type + ':\t' + msg + '\n')
