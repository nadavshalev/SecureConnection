import hashlib
import base64
import hmac
from Crypto import Random
from Crypto.Cipher import AES
import secrets

class AESCipher:
    """
    Symmetric AES encryption for data transfer part of ConnSecure protocol
    """

    # key length (AES 256)
    BS = 32

    def __init__(self, key=None):
        """
        :param key: None: must call gen_key() before use. Not None: load key from outside
        """
        self.key = None
        if key is not None:
            self.set_key(key)

    def set_key(self, key):
        if len(key) != self.BS:
            raise Exception("Error: aes key must be in length of BS")
        self.key = key

    def encrypt(self, raw):
        """
        Encrypt the data and set HMAC after encryption
        :param raw: data for encryption
        :return: encrypted message
        """
        raw = self.pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        enc_msg = iv + cipher.encrypt(raw)
        # set HMAC
        hmac = self.hmac_sha256(enc_msg)
        return base64.b64encode(enc_msg+hmac)

    def decrypt(self, enc):
        """
        Decrypt data and check HMAC
        :param enc: data to be decrypted
        :return: decrypted message
        """
        enc = base64.b64decode(enc)
        iv = enc[:16]
        msg_enc = enc[16:-32]

        # HMAC verify
        rx_hmac = enc[-32:]
        tx_hmax = self.hmac_sha256(iv+msg_enc)
        if tx_hmax != rx_hmac:
            raise RuntimeError('HMAC not fit!')

        # decode
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self.unpad(cipher.decrypt(msg_enc)).decode('utf8')

    def hmac_sha256(self, msg):
        return hmac.new(self.key, msg, digestmod=hashlib.sha256).digest()

    def unpad(self, s):
        return s[0:-ord(s[-1:])]

    def pad(self, s):
        return bytes(s + (self.BS - len(s) % self.BS) * chr(self.BS - len(s) % self.BS), 'utf-8')

    def gen_key(self):
        """
        Generate random key using secrets module
        :return: key
        """
        key = secrets.token_urlsafe(self.BS)
        self.key = hashlib.sha256(key.encode()).digest()

