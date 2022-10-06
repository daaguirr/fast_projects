import os
import time
from pathlib import Path

from environs import Env

from utils import format_number

env = Env()
env.read_env()

with env.prefixed("TAGS_"):
    PATH = env.str("PATH")
    ARTIST = env.str("ARTIST")
    ALBUM = env.str("ALBUM")
    COVER_PATH = env.str("COVER_PATH")


def main():
    pathlist = Path(PATH).rglob('*.mp3')

    files = []

    for path in pathlist:
        path_in_str = str(path)
        files.append(path_in_str)

    files.sort()

    print(files)
    input("Press Enter to continue...")

    for i, file in enumerate(files):
        import eyed3

        p = Path(file)
        audiofile = eyed3.load(file)
        # if audiofile.tag is None:
        audiofile.initTag()

        audiofile.tag.artist = ARTIST
        audiofile.tag.album = ALBUM
        audiofile.tag.album_artist = ARTIST
        audiofile.tag.title = f"{ALBUM} {format_number(i + 1, len(files))}"
        audiofile.tag.track_num = i + 1
        audiofile.tag.images.set(3, open(COVER_PATH, 'rb').read(), 'image/jpeg')
        audiofile.tag.save()
        os.rename(file, os.path.join(p.parent, f"{format_number(i + 1, len(files))}.mp3"))

        time.sleep(0.01)


if __name__ == '__main__':
    main()
