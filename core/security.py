import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class Security:
    def __init__(self, key: str = None):
        if key:
            self._key = self._derive_key(key)
        else:
            self._key = AESGCM.generate_key(bit_length=256)

    def _derive_key(self, password: str) -> bytes:
        salt = b'kifzl_dev_bot_salt'
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return kdf.derive(password.encode())

    def encrypt(self, plaintext: str) -> str:
        aesgcm = AESGCM(self._key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
        return base64.b64encode(nonce + ciphertext).decode()

    def decrypt(self, encrypted: str) -> str:
        try:
            data = base64.b64decode(encrypted.encode())
            nonce = data[:12]
            ciphertext = data[12:]
            aesgcm = AESGCM(self._key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext.decode()
        except Exception:
            return None

    @staticmethod
    def generate_random_code(length: int = 12) -> str:
        import string
        import random
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
