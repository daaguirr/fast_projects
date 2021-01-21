import os
import re

from environs import Env
from pydub import AudioSegment
from tqdm import trange

env = Env()
env.read_env()

with env.prefixed("CREATE_"):
    FOLDER_NAME = env.str("OUTPUT_WAV_PATH")
    FOLDER_OUTPUT = env.str("OUTPUT_MP3_PATH")
    PREFIX = env.str("PREFIX_NAME")

if not os.path.exists(FOLDER_OUTPUT):
    os.makedirs(FOLDER_OUTPUT, exist_ok=True)

PREFIX_FILES_REGEX, PREFIX_FILES_REGEX_FN = \
    rf"{PREFIX}(\d\d\d|\d\d)\w\.wav$", lambda _chapter: rf"{PREFIX}{_chapter}\w\.wav$"

files = [f for f in os.listdir(FOLDER_NAME) if re.search(PREFIX_FILES_REGEX, f)]
chapters = sorted(list(set([re.match(PREFIX_FILES_REGEX, f).group(1) for f in files])))

for i in trange(len(chapters)):
    chapter = chapters[i]
    inner_regex = PREFIX_FILES_REGEX_FN(chapter)
    filtered = sorted([f for f in files if re.search(inner_regex, f)])
    print(filtered)
    filtered = [os.path.join(FOLDER_NAME, f) for f in filtered]

    playlist_songs = [AudioSegment.from_wav(f) for f in filtered]
    combined = AudioSegment.empty()
    for song in playlist_songs:
        combined += song

    combined.export(os.path.join(FOLDER_OUTPUT, f"{chapter}.mp3"), format="mp3", bitrate="192k")
