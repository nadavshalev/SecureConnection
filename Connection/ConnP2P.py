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
        'closed_connection': 'closed_connection_from_address'
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
        if not self.connected:
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
        if not self.connected:
            self.log('Error (receive): not connected')
            raise ConnectionError('not connected')

        try:
            data_str = self.s.receive()
            if not data_str:
                raise ConnectionError('base connection ended unexpectedly')

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
        d = {
            'data': msg,
            'addr': {
                'to': to_,
                'from': from_
            }
        }
        return json.dumps(d)

    def decode(self, data):
        msg = json.loads(data)
        addr = msg['addr']
        msg_data = msg['data']
        to_ = addr['to']
        from_ = addr['from']
        return msg_data, to_, from_


class ConnP2PClient(ConnP2P):

    def __init__(self, base_conn, my_addr, log_file):
        ConnP2P.__init__(self, base_conn, my_addr, log_file)

    def connect(self, conn_addr=None):
        if self.connected:
            self.log('Warning (connect): already connected')
            return True

        # set lower connection
        if not self.s.connect():
            return False

        try:
            self.connected = True

            # try to connect to address
            if conn_addr:
                # case already connected
                if self.conn_addr:
                    self.log('Error (connect): already connected to address')
                    self.disconnect()
                    return False

                # send request to server
                self.conn_addr = conn_addr
                # set connection (BLOCKING) raise error if fails
                if not self.set_new_connection():
                    return False
            else:
                # waits for connection (BLOCKING)
                if not self.set_wait_connection():
                    return False

        except Exception as e:
            self.log("Error (connect): can't connect - " + repr(e))
            self.disconnect()
            return False

        return True

    def disconnect(self):
        if self.s.connected:
            # send close request (should not fail)
            try:
                self.send(self.P['request_close_connection'], hard_fail=True)
            except:
                pass
        self.clear_connection()
        self.log('Success (disconnect)')

    def set_new_connection(self):
        # send request for new connection
        self.send(self.P['request_new_connection'])

        # receive response from server
        data = self.receive()

        # case server didn't accept
        if data != self.P['accept_connection']:
            self.log('Error (set_new_connection): connection denied by server: ' + repr(data))
            self.disconnect()
            return False
        return True

    def set_wait_connection(self):
        # send request for new connection
        self.send(self.P['wait_for_connection'])

        # receive response from server
        data = self.receive()

        # case server didn't accept
        if data != self.P['accept_connection']:
            self.log('Error (set_wait_connection): connection denied by server: ' + repr(data))
            self.disconnect()
            return False
        return True

    def send(self, msg, hard_fail=False):
        msg = self.encode(msg, to_=self.conn_addr, from_=self.my_addr)
        ConnP2P.send(self, msg, hard_fail)

    def receive(self):
        data, to_, from_ = ConnP2P.receive(self)

        if data == self.P['closed_connection']:
            self.clear_connection()
            self.log('State (run): connection ended by other')
            return None

        if not self.validate_receive(data, to_, from_):
            raise ConnectionError('validation failed')
        if not self.conn_addr:
            self.conn_addr = from_
        return data

    def clear_connection(self):
        # disconnect base connection
        if self.s.connected:
            self.s.disconnect()
        # clear data
        self.conn_addr = None
        # set state to disconnected
        self.connected = False


class ConnP2PServer(ConnP2P):

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
            self.log("Error (connect): can't connect - " + repr(e))
            self.disconnect()
            return False

        return True

    def run(self, other):
        while True:
            data, to_, from_ = self.receive()
            if not self.validate_receive(data, from_, to_):
                break

            # disconnected
            if data == self.P['request_close_connection']:
                self.disconnect()
                self.log('State (run): connection ended by user')
                break

            msg = other.encode(data, to_=other.my_addr, from_=self.my_addr)
            other.send(msg)

    def disconnect(self):
        if self.s.connected:
            try:
                self.send(self.P['closed_connection'], hard_fail=True)
            except:
                pass
            try:
                self.conn_obj.send(self.P['closed_connection'], hard_fail=True)
            except:
                pass
            self.s.disconnect()
        self.log('Success (disconnect)')
