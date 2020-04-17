from Connection import ConnInterface
import socket
import datetime

"""
============== Class Socket =============
global Implementations:
    disconnect()
    send()
    receive()
"""
class ConnSocket(ConnInterface):
    PACK_SIZE = 4096

    def __init__(self, log_file):
        ConnInterface.__init__(self, log_file)
        self.type = 'socket'
        self.s = None

    def connect(self):
        raise NotImplementedError

    def disconnect(self):
        if not self.connected:
            return

        try:
            self.s.close()
        except Exception as e:
            self.log('Warning (disconnect): ' + repr(e))
        self.s = None
        self.connected = False
        self.log('Success (disconnect)')

    def send(self, msg):
        if not self.connected:
            self.log('Error (send): not connected')
            raise ConnectionError('not connected')
        try:
            if type(msg) == str:
                msg = msg.encode()

            total_sent = 0
            while total_sent < len(msg):
                sent = self.s.send(msg[total_sent:])
                if sent == 0:
                    raise ConnectionError("socket connection broken")
                total_sent = total_sent + sent
        except Exception as e:
            self.disconnect()
            self.log('Error (send): ' + repr(e))
            raise e

    def receive(self):
        if not self.connected:
            self.log('Error (receive): not connected')
            raise ConnectionError('not connected')

        try:
            data = self.s.recv(self.PACK_SIZE)
        except Exception as e:
            self.disconnect()
            self.log('Error (receive): ' + repr(e))
            raise e

        if not data:
            self.disconnect()
            self.log('State (receive): connection ended by host')
            return None

        return data

    def get_addr(self):
        try:
            return self.s.getsockname()
        except:
            return ('0.0.0.0', '00000')


"""
============== Client Socket =============
connect to socket by 5-tuple
must call connect()
"""
class ConnSocketClient(ConnSocket):
    def __init__(self, ip, port, log_file):
        ConnInterface.__init__(self, log_file)
        self.type = 'socket'
        self.ip = ip
        self.port = port
        self.s = None

    def connect(self):
        if self.connected:
            self.log('Warning (connect): already connected')
            return True

        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect((self.ip, self.port))
        except Exception as e:
            self.log("Error (connect): can't connect socket - " + repr(e))
            self.disconnect()
            return False

        self.connected = True
        self.log('Success (connect)')
        return True

    def log(self, msg):
        self.log_file.write(str(datetime.datetime.now()) + '\t' + repr(self.get_addr()) + '\t' + self.type + ':\t\t' + msg + '\n')

"""
============== Server Socket =============
connect to socket by accept() and then create class instance
can't call connect() - already connected
when disconnect(): must exit and create new instance after server connect a new socket
"""
class ConnSocketServer(ConnSocket):
    def __init__(self, conn, log_file, addr):
        ConnInterface.__init__(self, log_file)
        self.type = 'socket'
        self.s = conn
        self.addr = addr
        self.connected = True

    def log(self, msg):
        self.log_file.write(str(datetime.datetime.now()) + '\t' + repr(self.addr) + '\t' + self.type + ':\t\t' + msg + '\n')
