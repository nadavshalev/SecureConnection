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
    HEADER_LEN = 5  # 2^(5*8)=2^40=Tara

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
        self.connected = False
        self.log('Success (disconnect)')

    def send(self, msg: bytes):
        if not self.connected:
            self.log('Error (send): not connected')
            raise ConnectionError('not connected')
        try:
            # case msg is empty (will look like socket closed)
            if msg == b'':
                msg = b' '

            # transmit msg length in HEADER_LEN first bytes
            msg_size = len(msg)
            if msg_size > 2 ** (8 * self.HEADER_LEN) - 1:
                raise RuntimeError('message is too big for transmission')

            header = self.create_header(msg_size)
            msg = header + msg

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

    def receive(self) -> bytes:
        if not self.connected:
            self.log('Error (receive): not connected')
            raise ConnectionError('not connected')

        try:
            header_data = self.s.recv(self.HEADER_LEN)
            if not header_data or not self.connected:
                self.disconnect()
                self.log('State (receive): connection ended by host')
                return b''

            msg_len = self.decode_header(header_data)

            data = []
            bytes_recd = 0
            while bytes_recd < msg_len:
                chunk = self.s.recv(min(msg_len - bytes_recd, self.PACK_SIZE))
                if chunk == b'':
                    raise RuntimeError("socket connection broken")
                data.append(chunk)
                bytes_recd = bytes_recd + len(chunk)

        except Exception as e:
            self.disconnect()
            self.log('Error (receive): ' + repr(e))
            raise e

        return b''.join(data)

    def get_addr(self):
        try:
            return self.s.getsockname()
        except:
            return ('0.0.0.0', '00000')

    def create_header(self, x: int) -> bytes:
        return x.to_bytes(self.HEADER_LEN, 'big')

    def decode_header(self, xbytes: bytes) -> int:
        return int.from_bytes(xbytes, 'big')


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
