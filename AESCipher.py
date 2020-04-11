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
        enc_msg = iv + cipher.encrypt(raw)
        # set HMAC
        hmac = self.hmac_sha256(enc_msg)
        return base64.b64encode(enc_msg+hmac)

    def decrypt(self, enc):
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
        key = secrets.token_urlsafe(self.BS)
        self.key = hashlib.sha256(key.encode()).digest()


# aes1 = AESCipher()
# aes1.gen_key()
# aes2 = AESCipher()
# aes2.gen_key()
#
# enc = aes1.encrypt('Hello World')
# print(enc)
# print(len(enc))
# msg = aes2.decrypt(enc)
# print(msg)
# print(len(msg))
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
