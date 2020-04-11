from abc import ABC, abstractmethod
import datetime

class ConnInterface(ABC):
    connected = False
    type = 'interface'

    def __init__(self, log_file):
        self.log_file = log_file

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
    def send(self, msg):
        """
        send all data reliably
        :raise: ConnectionError
        """
        pass

    @abstractmethod
    def receive(self) -> str:
        """
        get message
        :raise: ConnectionError
        :return: received message[str] or None if Closed
        """
        pass

    def log(self, msg):
        self.log_file.write(str(datetime.datetime.now()) + '\t' + self.type + ':\t' + msg + '\n')