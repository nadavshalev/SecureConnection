from Crypto.PublicKey import RSA
from Crypto import Random
from Crypto.Cipher import PKCS1_OAEP


class RSAPrivate:
    """
    Create Private RSA key - can both encrypt and decrypt
    Use in server side (ConnSecure)
    """
    def __init__(self, key_size=3072):
        random_generator = Random.new().read
        self.private_key = RSA.generate(key_size, random_generator)
        self.public_key = self.private_key.publickey()
        self.decryptor = PKCS1_OAEP.new(self.private_key)
        self.encryptor = PKCS1_OAEP.new(self.public_key)

    def decrypt(self, enc):
        return self.decryptor.decrypt(enc)

    def encrypt(self, msg):
        return self.encryptor.encrypt(msg)

    def export_public(self):
        return self.public_key.exportKey()

    def export_private(self):
        return self.private_key.exportKey()


class RSAPublic:
    """
    Only load RSA public key - can't decrypt
    Use in client side (ConnSecure)
    """
    def __init__(self):
        self.public_key = None
        self.encryptor = None

    def load_key(self, pub_key):
        self.public_key = RSA.importKey(pub_key)
        self.encryptor = PKCS1_OAEP.new(self.public_key)

    def encrypt(self, msg):
        return self.encryptor.encrypt(msg)
