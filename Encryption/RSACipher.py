from Crypto.PublicKey import RSA
from Crypto import Random
from Crypto.Cipher import PKCS1_OAEP


class RSAPrivate:
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

    def __init__(self):
        self.public_key = None
        self.encryptor = None

    def load_key(self, pub_key):
        self.public_key = RSA.importKey(pub_key)
        self.encryptor = PKCS1_OAEP.new(self.public_key)

    def encrypt(self, msg):
        return self.encryptor.encrypt(msg)



# rsa_private = RSAPrivate()
# pubKey = rsa_private.export_public()
#
# rsa_public = RSAPublic(pubKey)
#
# enc = rsa_public.encrypt(b'bla bla bla hello world')
#
# msg = rsa_private.decrypt(enc)
#
# print(msg)

