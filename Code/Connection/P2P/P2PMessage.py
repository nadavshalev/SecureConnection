class P2PMessage:
    DELIM = '!~!'

    def __init__(self, data: bytes, to_: str = '', from_: str = ''):
        self.data = data
        self.to_ = to_
        self.from_ = from_

    def validate(self):
        pass

    def encode(self) -> bytes:
        header = self.to_ + self.DELIM + self.from_ + self.DELIM
        msg = [header.encode(), self.data]
        return b''.join(msg)

    @staticmethod
    def decode(data: bytes):
        data_split = data.split(P2PMessage.DELIM.encode(), 2)
        if len(data_split) != 3:
            raise ValueError('cant split to 3')
        return P2PMessage(data_split[2], data_split[0].decode(), data_split[1].decode())
