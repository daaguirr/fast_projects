import argparse
import getpass
import os

import pyAesCrypt
from cryptography.fernet import Fernet
import base64


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file',
                        required=True, type=str)
    parser.add_argument('--chunk',
                        required=False, type=int, default=64 * 1024)
    print("Enter password to encrypt or None if generate random")
    pw = getpass.getpass()
    pw = None if pw == '' or pw == os.linesep else pw
    args = parser.parse_args()
    data_path = args.file
    chunk_size = int(args.chunk)

    key: str = pw if pw is not None else Fernet.generate_key().decode()

    pyAesCrypt.encryptFile(data_path, f"{data_path}.encrypted", key, chunk_size)

    if pw is None:
        print(key)


if __name__ == '__main__':
    main()
