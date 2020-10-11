import getpass

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
import os
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--key_file',
                        required=True)
    parser.add_argument('--file',
                        required=True)

    args = parser.parse_args()
    key_file_path = args.key_file
    data_path = args.file

    print("Enter password of private key:")
    pw = getpass.getpass()

    with open(key_file_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=pw.encode(),
            backend=default_backend()
        )

    with open(data_path, "rb") as file:
        header_size = file.readline()
        header = file.read(int(header_size))
        data = file.read()

        key = private_key.decrypt(
            header,
            padding.OAEP(

                mgf=padding.MGF1(algorithm=hashes.SHA256()),

                algorithm=hashes.SHA256(),

                label=None
            )
        )
        f = Fernet(key)
        decrypted_data = f.decrypt(data)
        filename = os.path.splitext(file.name)[0]
        with open(f"out_{filename}", 'wb') as out_file:
            out_file.write(decrypted_data)
