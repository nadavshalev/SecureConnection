from Connection.P2P import ConnP2P


class ConnP2PClient(ConnP2P):

    def __init__(self, base_conn, my_addr, log_file, conn_addr=None):
        ConnP2P.__init__(self, base_conn, my_addr, log_file)
        self.conn_addr = conn_addr

    def connect(self):
        if self.connected:
            self.log('Warning (connect): already connected')
            return True

        # set lower connection
        if not self.s.connect():
            return False

        try:
            self.connected = True

            # try to connect to address
            if self.conn_addr:

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

        self.log('Success (connect)')
        return True

    def disconnect(self):
        if not self.connected:
            return

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

    def send(self, msg: bytes, hard_fail=False):
        msg = self.encode(msg, to_=self.conn_addr, from_=self.my_addr)
        ConnP2P.send(self, msg, hard_fail)

    def receive(self) -> bytes:
        data, to_, from_ = ConnP2P.receive(self)

        # case connection already closed
        if not self.connected:
            return b''

        if data == self.P['closed_connection']:
            # self.send(self.P['closed_connection_accepted'])
            self.clear_connection()
            self.log('State (receive): connection ended by other')
            return b''

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