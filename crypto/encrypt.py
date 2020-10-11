from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--key_file',
                        required=True)
    parser.add_argument('--file',
                        required=True)

    args = parser.parse_args()
    key_file_path = args.key_file

    with open(key_file_path, "rb") as key_file:
        public_key = serialization.load_pem_public_key(
            key_file.read(),
            backend=default_backend()
        )
    data_path = args.file
    with open(data_path, "rb") as file:
        image = file.read()

    key: bytes = Fernet.generate_key()
    fernet = Fernet(key)

    encrypted_key: bytes = public_key.encrypt(
        key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    encrypted_file = fernet.encrypt(image)

    with open(f"{data_path}.encrypted", "wb") as file:
        file.write(f"{len(encrypted_key)}\n".encode())
        file.write(encrypted_key)
        file.write(encrypted_file)
