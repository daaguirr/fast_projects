import os
import re
from pathlib import Path

from environs import Env

from utils import audios_from_file

env = Env()
env.read_env()

with env.prefixed("DAISY2MP3_"):
    PATH = env.str("PATH")


def main():
    pathlist = Path(PATH).rglob('*.smil')

    files = []

    for path in pathlist:
        path_in_str = str(path)
        if 'master' not in path_in_str:
            files.append(path_in_str)

    for f in files:
        tmp = audios_from_file(f)
        if len(tmp) > 1:
            raise Exception('Unsupported')
        try:
            number = re.match(r".*ptk(.*)\.", f).group(1)[-3:]
        except:
            number = re.match(r"(.*)\.", f).group(1)[-3:]
        audio_file = os.path.join(PATH, audios_from_file(f)[0])
        os.rename(audio_file, os.path.join(PATH, f"{number}.mp3"))


if __name__ == '__main__':
    main()
