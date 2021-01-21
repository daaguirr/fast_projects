from pathlib import Path
from environs import Env

import bs4
import re
import os

env = Env()
env.read_env()

with env.prefixed("DAISY2MP3_"):
    PATH = env.str("PATH")


def audios_from_file(path):
    import codecs

    with codecs.open(path, mode="r", encoding="iso-8859-1") as f:
        soup = bs4.BeautifulSoup(f.read(), "lxml")

    unique = set()
    for a in soup.find_all('audio'):
        unique.add(a.get('src'))
    unique = list(unique)
    return unique


def main():
    pathlist = Path(PATH).rglob('*.smil')

    files = []

    for path in pathlist:
        # because path is object not string
        path_in_str = str(path)
        if 'master' not in path_in_str:
            files.append(path_in_str)

    for f in files:
        if len(audios_from_file(f)) > 1:
            raise Exception('Unsupported')

    mapping = {}
    for f in files:
        p = Path(f)
        number = re.match(r".*ptk(.*)\.", f).group(1)[-3:]
        # number = re.match(r"(.*)\.", f).group(1)[-3:]
        audio_file = os.path.join(p.parent, audios_from_file(f)[0])
        mapping[number] = audio_file
        os.rename(audio_file, os.path.join(p.parent, f"{number}.mp3"))


if __name__ == '__main__':
    main()
