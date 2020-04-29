import threading
from abc import ABCMeta

from Connection.P2P import ConnP2P


class ConnP2PServer(ConnP2P, metaclass=ABCMeta):

    def __init__(self, base_conn, conn_dict, log_file):
        # set connection (my_addr = None)
        ConnP2P.__init__(self, base_conn, None, log_file)
        # contain all waiting connections
        self.conn_dict = conn_dict
        self.conn_obj = None

    def start(self):

        # set lower connection
        if not self.s.connect():
            self.log('Error (start): lower failed to connect')
            return False

        try:
            self.connected = True
            # receive connection params from user
            conn_type, conn_addr, my_addr = self.receive()
            # set current address
            self.my_addr = my_addr

            # case try to connect to other user
            if conn_type == self.P['request_new_connection']:
                # check if user in dict
                if conn_addr not in self.conn_dict:
                    self.log("Error (start): requested address not active: ")
                    self.disconnect()
                    return False

                # set other address
                self.conn_addr = conn_addr

                # set other P2Pobj as param and delete from dict
                self.conn_obj = self.conn_dict[conn_addr]
                del self.conn_dict[conn_addr]

                # set own address in conn_obj
                self.conn_obj.conn_addr = self.my_addr
                self.conn_obj.conn_obj = self

                # set accept_connection message to the users
                msg = self.encode(self.P['accept_connection'], to_=self.my_addr, from_=self.conn_addr)
                self.send(msg)
                msg = self.encode(self.P['accept_connection'], to_=self.conn_addr, from_=self.my_addr)
                self.conn_obj.send(msg)

                # start other listen on thread
                threading.Thread(target=self.conn_obj.run, args=(self,)).start()
                # start current listen
                self.run(self.conn_obj)

            elif conn_type == self.P['wait_for_connection']:
                if self.my_addr in self.conn_dict:
                    self.log("Error (start): user identifier already wait for connections: ")
                    self.disconnect()
                    return False
                self.conn_dict[self.my_addr] = self
            else:
                self.log("Error (start): connection type wrong: " + repr(conn_type))
                self.disconnect()
                return False

        except Exception as e:
            self.log("Error (start): while running - " + repr(e))
            self.disconnect()
            return False

        return True

    def run(self, other):
        self.log('Success (run)')
        while True:
            try:
                data, to_, from_ = self.receive()

                if not self.connected or not data:
                    break

                if not self.validate_receive(data, from_, to_):
                    self.log('Error (run): validation failed')
                    self.disconnect()
                    break

                # disconnected
                if data == self.P['request_close_connection']:
                    self.log('State (run): connection ended by user')
                    self.disconnect()
                    break

                msg = other.encode(data, to_=other.my_addr, from_=self.my_addr)
                other.send(msg)
            except Exception as e:
                self.log("Error (run): " + repr(e))
                self.disconnect()
                break

        print(f'exit run() thread: {self.my_addr}')

    def disconnect(self):
        if not self.connected:
            return

        self.s.disconnect()

        self.connected = False

        # if still connected - disconnect from pair connection
        if self.conn_obj:
            self.conn_obj.destroy()

        self.log('Success (disconnect)')

    def destroy(self):
        if not self.connected:
            return

        try:
            # try send close request and disconnect
            if self.s.connected:
                msg = self.encode(self.P['closed_connection'], to_=self.my_addr, from_=self.conn_addr)
                self.send(msg, hard_fail=True)
                self.s.disconnect()
        except:
            pass

        self.connected = False
        self.log('Success (destroy)')
