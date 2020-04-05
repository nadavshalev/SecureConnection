import hashlib
import base64
import hmac
from Crypto import Random
from Crypto.Cipher import AES
import secrets

class AESCipher:

    BS = 32
    key = None

    def __init__(self, key=None):
        if key is not None:
            self.set_key(key)

    def set_key(self, key):
        if len(key) != self.BS:
            raise Exception("Error: aes key must be in length of BS")
        self.key = key

    def encrypt(self, raw):
        raw = self.pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw))

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:16]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self.unpad(cipher.decrypt(enc[16:])).decode('utf8')

    def hmac_sha256(self, msg):
        return base64.b64encode(hmac.new(self.key, msg, digestmod=hashlib.sha256).digest())

    def unpad(self, s):
        return s[0:-ord(s[-1:])]

    def pad(self, s):
        return bytes(s + (self.BS - len(s) % self.BS) * chr(self.BS - len(s) % self.BS), 'utf-8')

    def gen_key(self):
        key = secrets.token_urlsafe(self.BS)
        self.key = hashlib.sha256(key.encode()).digest()


# aes1 = AESCipher()
# aes1.gen_key()
# print(b'KEY: ' + aes1.key)
# print(len(aes1.key))
# msg = 'OCB is by far the best mode, as it allows encryption and authentication in a single pass. However there are ' \
#       'patents on it in USA. The only thing '
#
# enc = aes1.encrypt(msg)
# hmac1 = aes1.hmac_sha256(enc)
#
# encTxt = base64.b64decode(enc)
# print(b'ENC: ' + encTxt[:16])
# print()
# print(b'HMAC: ' + hmac1)
#
# aes2 = AESCipher(aes1.key)
#
# hmac2 = aes2.hmac_sha256(enc)
# dec = aes2.decrypt(enc)
# print('DEC: ' + dec)
#
# print(hmac1 == hmac2)
