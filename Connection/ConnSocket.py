from Connection.ConnInterface import ConnInterface
import socket


class ConnSocket(ConnInterface):
    PACK_SIZE = 1024

    def __init__(self, ip, port, log_file):
        ConnInterface.__init__(self, log_file)
        self.type = 'socket'
        self.ip = ip
        self.port = port
        self.s = None

    def connect(self):
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect((self.ip, self.port))
        except:
            self.log("Error (connect): can't connect socket")
            self.disconnect()
            return False
        self.connected = True
        return True

    def disconnect(self):
        if self.connected:
            try:
                self.s.close()
            except Exception as e:
                self.log('Warning (disconnect): ' + repr(e))
        self.s = None
        self.connected = False

    def send(self, msg):
        if not self.connected:
            self.log('Error (send): not connected')
            raise ConnectionError('not connected')
        try:
            total_sent = 0
            while total_sent < len(msg):
                sent = self.s.send(msg[total_sent:])
                if sent == 0:
                    raise ConnectionError("socket connection broken")
                total_sent = total_sent + sent
                print(sent)
        except Exception as e:
            self.disconnect()
            self.log('Error (send): ' + repr(e))
            raise ConnectionError(str(e))

    def receive(self):
        if not self.connected:
            self.log('Error (receive): not connected')
            raise ConnectionError('not connected')

        try:
            data = self.s.recv(self.PACK_SIZE)
        except Exception as e:
            self.disconnect()
            self.log('Error (receive): ' + repr(e))
            raise ConnectionError(str(e))

        if not data:
            self.disconnect()
            self.log('State (receive): connection ended by host')
            return None

        return data


# f = open('log_conn.txt', 'a')
# c = ConnSocket('127.0.0.1',65432, f)
# print(type(c) == ConnSocket)
# print(c.connected)
# print(c.connect())
# c.send(b'bla bla')
# print(c.receive())
# f.close()