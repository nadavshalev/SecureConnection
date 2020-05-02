import threading
from abc import ABCMeta, ABC

from Connection.P2P import ConnP2P, P2PMessage
import queue


class ConnP2PServer(ConnP2P):
    MSG_CONN_CLOSED = b'123rc132dx13rc'

    def __init__(self, base_conn, conn_dict, log_file):
        # set connection (my_addr = None)
        ConnP2P.__init__(self, base_conn, None, log_file)
        # contain all waiting connections
        self.conn_dict = conn_dict
        self.conn_obj = None

    def run(self):

        # set lower connection
        if not self.s.connect():
            self.log('Error (start): lower failed to connect')
            return False

        try:

            # receive username
            # TODO: user auth
            username = self.s.receive()
            self.username = username.decode()

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
        while True:
            try:
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
        while True:
            try:
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

        self.s.disconnect()

        # wake up send thread for close
        if self.username in self.conn_dict:
            msg = P2PMessage(self.MSG_CONN_CLOSED)
            self.conn_dict[self.username].put(msg)

        self.connected = False

        self.log('Success (disconnect_from_receive)')

    def disconnect_from_send(self):

        # also wake up receive thread because sock.shutdown
        self.s.disconnect()

        if self.username in self.conn_dict:
            del self.conn_dict[self.username]

        self.connected = False

        self.log('Success (disconnect_from_send)')
