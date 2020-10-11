import argparse
import getpass
import os

import pyAesCrypt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file',
                        required=True, type=str)
    parser.add_argument('--chunk',
                        required=False, type=int, default=64 * 1024)
    print("Enter password to decrypt")
    pw = getpass.getpass()

    args = parser.parse_args()
    data_path = args.file
    chunk_size = int(args.chunk)

    filename, _ = os.path.splitext(data_path)
    filename_real, extension_real = os.path.splitext(filename)

    pyAesCrypt.decryptFile(data_path, f"{filename_real}_decrypted{extension_real}", pw, chunk_size)


if __name__ == '__main__':
    main()
