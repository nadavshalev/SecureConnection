import threading
from abc import ABCMeta, ABC

from Connection.P2P import ConnP2P, P2PMessage
import queue


class ConnP2PServer(ConnP2P):
    """
    Create secure channel with specific user.
    Listen on user's channel and rout his messages to other users input queue
    Listen on user's input queue for messages from other users and sent it throw his channel
    """

    MSG_CONN_CLOSED = b'123rc132dx13rc'

    def __init__(self, base_conn, conn_dict, log_file):
        # set connection (my_addr = None)
        ConnP2P.__init__(self, base_conn, None, log_file)

        # contain all running connections
        self.conn_dict = conn_dict
        self.conn_obj = None

    def run(self):
        """
        Connect to user with secure channel.
        Listen on channel for outgoing messages.
        Listen on buffer for incoming messages.
        """

        # set lower connection
        if not self.s.connect():
            self.log('Error (start): lower failed to connect')
            return False

        try:

            # TODO: user auth

            # receive username
            username = self.s.receive()
            self.username = username.decode()

            # create new entrance in running users dict
            self.conn_dict[self.username] = queue.Queue()

            self.connected = True

            # start wait for messages to send to this conn
            threading.Thread(target=self.send_to_conn).start()

            # start listen on this conn
            self.receive_from_conn()

        except Exception as e:
            self.log("Error (start): while running - " + repr(e))
            self.disconnect()
            return False

        self.connected = True
        return True

    def receive_from_conn(self):
        """
        Get outgoing messages from channel and pass them to the correct input queue
        """

        while True:
            try:
                # receive from channel (BLOCKING)
                data = self.receive()

                # decode msg
                msg = P2PMessage.decode(data)
                msg.from_ = self.username

                # user ask to disconnect or connection failed
                if not self.connected or \
                        not msg.data or \
                        msg.data == self.REQUEST_CLOSE_CONNECTION:
                    self.log('State (receive_from_conn): connection ended')
                    self.disconnect_from_receive()
                    break

                if msg.to_ in self.conn_dict:
                    self.conn_dict[msg.to_].put(msg)
                else:
                    self.log(f"Warning (receive_from_conn): address {msg.to_} not found in active connections")

            except Exception as e:
                self.log("Error (receive_from_conn): while running - " + repr(e))
                self.disconnect_from_receive()
                break
        print(f'{self.username} exit receive')

    def send_to_conn(self):
        """
        Listen on income queue and send message to user channel
        """

        while True:
            try:
                # get income message (BLOCKING)
                msg = self.conn_dict[self.username].get()

                if not self.connected or msg.data == self.MSG_CONN_CLOSED:
                    self.log('State (send_to_conn): connection closed')
                    self.disconnect_from_send()
                    break

                self.send_(msg.encode())
            except Exception as e:
                self.log("Error (send_to_conn): while running - " + repr(e))
                self.disconnect_from_send()
                break

        print(f'{self.username} exit send')

    def disconnect_from_receive(self):
        """
        Disconnect when request got from receive thread
        """

        self.s.disconnect()

        # wake up send thread for close
        if self.username in self.conn_dict:
            msg = P2PMessage(self.MSG_CONN_CLOSED)
            self.conn_dict[self.username].put(msg)

        self.connected = False

        self.log('Success (disconnect_from_receive)')

    def disconnect_from_send(self):
        """
        Disconnect when request got from send thread
        """

        # also wake up receive thread because sock.shutdown
        self.s.disconnect()

        if self.username in self.conn_dict:
            del self.conn_dict[self.username]

        self.connected = False

        self.log('Success (disconnect_from_send)')
