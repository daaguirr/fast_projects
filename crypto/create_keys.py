import getpass
import uuid

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

if __name__ == '__main__':
    print("Enter password to private key:")
    cond = True
    pw: str
    while cond:
        pw = getpass.getpass()
        if len(pw) >= 8:
            print("Confirm your password:")
            pw2 = getpass.getpass()
            if pw == pw2:
                cond = False
            else:
                print("Password are not the same enter again the password:")
        else:
            print("password too short enter new password:")

    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    pem_prk = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.BestAvailableEncryption(pw.encode('utf-8'))
    )

    public_key = private_key.public_key()
    pem_pk = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    name = uuid.uuid4().hex
    with open(f'{name}_private.pem', 'wb') as f:
        f.write(pem_prk)

    with open(f'{name}_public.pem', 'wb') as f:
        f.write(pem_pk)
