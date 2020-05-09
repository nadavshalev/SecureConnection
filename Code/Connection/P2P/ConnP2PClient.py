import queue
import threading
from abc import ABCMeta

from Connection.P2P import ConnP2P, P2PMessage
from Connection.P2PSecure import P2PSecure


class ConnP2PClient(ConnP2P):
    """
    Create and manage all connections from other user.
    Open single secure channel to server.
    """

    REQUEST_CLOSE_USER_CONN = b'asd876tAS7sfi'

    def __init__(self, base_conn, username, conn_dict, log_file):
        ConnP2P.__init__(self, base_conn, username, log_file)
        # dictionary of all active users connections
        self.conn_dict = conn_dict

    def connect(self):
        """
        Set encrypted channel to server
        :return:
        """

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
        """
        Encrypt and send data to specific user.
        Secure connection is open automatically even in the first message
        :param data: data to send
        :param to_address: send to this user
        """

        # create message with addresses
        msg = P2PMessage(data, to_address, self.username)

        # check if connection already exist in dict, if not create entrance
        if msg.to_ not in self.conn_dict:
            self.conn_dict[msg.to_] = P2PSecure(self.username, self)
        msg.data = self.conn_dict[msg.to_].encrypt(msg.data)

        # send
        ConnP2P.send_(self, msg.encode())

    def row_send(self, data: bytes, to_address: str):
        """
        Send data without encryption - used for connection establishment
        :param data: data to send
        :param to_address: send to this user
        """
        msg = P2PMessage(data, to_address, self.username)
        ConnP2P.send_(self, msg.encode())

    def listen(self):
        """
        Listen and decode all received messages in non-blocking manner
        """
        threading.Thread(target=self.init_listen).start()

    def init_listen(self):
        """
        Listen to server port and decode each message acording to its user and keys
        """

        while True:
            try:
                # receive data from server (BLOCKING)
                data = self.receive()

                # decode msg
                msg = P2PMessage.decode(data)

                # if message not address to me - raise an error
                if msg.to_ != self.username:
                    raise ConnectionError('message received with wrong destination address')

                # case connection failed
                if not self.connected or not msg.data:
                    raise ConnectionError('connection ended')

                if msg.data == self.REQUEST_CLOSE_CONNECTION:
                    raise ConnectionError('connection ended')

                # if ask to close user-level connection
                if msg.data == self.REQUEST_CLOSE_USER_CONN:
                    if msg.from_ in self.conn_dict:
                        del self.conn_dict[msg.from_]
                    continue

                # if connection to in active connection list - create new instance
                if msg.from_ not in self.conn_dict:
                    self.conn_dict[msg.from_] = P2PSecure(self.username, self)

                # decrypt message.
                # handle establishing new connection automatically
                self.conn_dict[msg.from_].get(msg)

            except Exception as e:
                self.log("Error (get_from_conn): while running - " + repr(e))
                self.disconnect()
                break

    def add(self, msg):
        """
        Insert new (not encrypted) messages to object.
        :param msg: unencrypted message
        """
        if msg.to_ not in self.conn_dict:
            self.conn_dict[msg.to_] = P2PSecure(self.username, self)
        self.conn_dict[msg.to_].add(msg)

    def close(self, to_address):
        if to_address in self.conn_dict:
            self.send(self.REQUEST_CLOSE_USER_CONN, to_address)
            del self.conn_dict[to_address]

    def disconnect(self):
        """
        Disconnect from server entirely.
        Cant send or receive messages anymore
        """
        if not self.connected:
            return

        # disconnect from server
        if self.s.connected:
            # first inform all users
            for user in self.conn_dict:
                try:
                    self.close(user)
                except:
                    pass

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

