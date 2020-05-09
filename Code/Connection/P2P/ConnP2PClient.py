import queue
import threading
from abc import ABCMeta

from Connection.P2P import ConnP2P, P2PMessage
from Connection.P2PSecure import P2PSecure


class ConnP2PClient(ConnP2P):

    def __init__(self, base_conn, username, conn_dict, log_file):
        ConnP2P.__init__(self, base_conn, username, log_file)
        self.conn_dict = conn_dict

    def connect(self):
        if self.connected:
            self.log('Warning (connect): already connected')
            return True

        # set lower connection
        if not self.s.connect():
            return False

        try:
            self.connected = True

            # send request for new connection with username
            self.s.send(self.username.encode())

            # TODO: server auth

        except Exception as e:
            self.log("Error (connect): can't connect - " + repr(e))
            self.disconnect()
            return False

        self.log('Success (connect)')
        return True

    def send(self, data: bytes, to_address: str):
        msg = P2PMessage(data, to_address, self.username)
        if msg.to_ not in self.conn_dict:
            self.conn_dict[msg.to_] = P2PSecure(self.username, self)
        msg.data = self.conn_dict[msg.to_].encrypt(msg.data)
        ConnP2P.send_(self, msg.encode())

    def row_send(self, data: bytes, to_address: str):
        msg = P2PMessage(data, to_address, self.username)
        ConnP2P.send_(self, msg.encode())

    def listen(self):
        threading.Thread(target=self.init_listen).start()

    def init_listen(self):
        while True:
            try:
                data = self.receive()
                # decode msg
                msg = P2PMessage.decode(data)
                if msg.to_ != self.username:
                    raise ConnectionError('message received with wrong destination address')

                # case connection failed
                if not self.connected or not msg.data:
                    raise ConnectionError('connection ended')

                # if ask close connection
                if msg.data == self.REQUEST_CLOSE_CONNECTION:
                    if msg.from_ in self.conn_dict:
                        del self.conn_dict[msg.from_]
                else:
                    if msg.from_ not in self.conn_dict:
                        self.conn_dict[msg.from_] = P2PSecure(self.username, self)
                    self.conn_dict[msg.from_].get(msg)

            except Exception as e:
                self.log("Error (get_from_conn): while running - " + repr(e))
                self.destroy()
                break

    def add(self, msg):
        if msg.to_ not in self.conn_dict:
            self.conn_dict[msg.to_] = P2PSecure(self.username, self)
        self.conn_dict[msg.to_].add(msg)

    def disconnect(self):
        if not self.connected:
            return

        if self.s.connected:
            # send close request (should not fail)
            try:
                msg = P2PMessage(self.REQUEST_CLOSE_CONNECTION)
                self.send_(msg.encode(), hard_fail=True)
            except:
                pass
        self.destroy()
        self.log('Success (disconnect)')

    def destroy(self):
        # disconnect base connection
        if self.s.connected:
            self.s.disconnect()
        self.conn_dict = {}
        # set state to disconnected
        self.connected = False

