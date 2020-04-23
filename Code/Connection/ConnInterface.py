from abc import ABC, abstractmethod
import datetime


class ConnInterface(ABC):

    def __init__(self, log_file):
        self.log_file = log_file
        self.type = 'interface'
        self.connected = False

    @abstractmethod
    def connect(self) -> bool:
        """
        establish reliable connection
        set self.connected -> True
        :return: success[True/False]
        """
        pass

    @abstractmethod
    def disconnect(self):
        """
        end connection and delete all data variables.
        set self.connected -> False.
        can't fail.
        """
        pass

    @abstractmethod
    def send(self, msg: bytes):
        """
        send all data reliably
        :raise: ConnectionError (disconnect before)
        """
        pass

    @abstractmethod
    def receive(self) -> bytes:
        """
        get message
        :raise: ConnectionError (disconnect before)
        :return: received message[str] or None if Closed
        """
        pass

    def get_addr(self) -> str:
        """
        :return: address in current layer
        """
        pass

    def log(self, msg):
        self.log_file.write(str(datetime.datetime.now()) + '\t' + self.type + ':\t' + msg + '\n')