from cryptography.fernet import Fernet

from python.utils import paths


def generateKeyToFile() -> None:
    # Generate a new key
    key = Fernet.generate_key()

    # Save the key to a file
    # write to file and truncate it
    # binary mode
    with open('secret.key', 'wb') as f:
        f.write(key)


def loadKey() -> bytes:
    with open(paths.resourcePath('secret.key'), 'rb') as f:
        return f.read()


def encryptText(text: str, key: bytes) -> bytes:
    fernet = Fernet(key)
    encrypted = fernet.encrypt(text.encode())
    return encrypted


def decryptText(text: str, key: bytes) -> str:
    fernet = Fernet(key)
    decrypted = fernet.decrypt(text).decode()
    return decrypted
