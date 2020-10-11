import json
import os
import re

from pydub import AudioSegment
from tqdm import trange

with open("create_audiobook.config.json", "r") as f:
    config = json.load(f)

FOLDER_NAME = config["OUTPUT_WAV_PATH"]
FOLDER_OUTPUT = config["OUTPUT_MP3_PATH"]
PREFIX = config["PREFIX_NAME"]

if not os.path.exists(FOLDER_OUTPUT):
    os.makedirs(FOLDER_OUTPUT, exist_ok=True)

PREFIX_FILES_REGEX, PREFIX_FILES_REGEX_FN = \
    f"{PREFIX}(\d\d)\w\.wav$", lambda chapter: f"{PREFIX}{chapter}\w\.wav$"

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
