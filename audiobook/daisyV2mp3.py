import os

from environs import Env

from utils import read_smil, format_number, audios_from_file

env = Env()
env.read_env()

with env.prefixed("DAISY2MP3_"):
    PATH = env.str("PATH")


def get_all_files():
    master_file = os.path.join(PATH, "master.smil")
    soup = read_smil(master_file)

    all_files = []
    for a in soup.find_all('ref'):
        all_files.append(os.path.join(PATH, a.get('src')))
    return all_files


def main():
    files = get_all_files()

    audio_files = []
    for f in files:
        tmp = audios_from_file(f)
        if len(tmp) > 1:
            raise Exception('Unsupported')
        audio_files = os.path.join(PATH, tmp[0])

    for i, audio_file in enumerate(audio_files):
        number = format_number(i + 1, len(files))
        os.rename(audio_file, os.path.join(PATH, f"{number}.mp3"))


if __name__ == '__main__':
    main()
