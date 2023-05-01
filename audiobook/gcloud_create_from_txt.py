# -*- coding: utf-8 -*-
import os
import re
import time

from bs4 import BeautifulSoup
from environs import Env
from google.cloud import texttospeech
from tqdm import trange

from utils import create_chapter, CreateChapterParams, base_build_name, base_format_number_fn

env = Env()
env.read_env()

with env.prefixed("CREATE_"):
    FOLDER_NAME = env.str("OUTPUT_PATH")
    FILE_TXT_PATH = env.str("FILE_TXT_PATH")
    TOKEN = env.str("TOKEN")
    PREFIX_NAME = env.str("PREFIX_NAME")
    VOICE = env.str("VOICE")
    LANG = env.str("LANG")

START_TOKEN = f"<{TOKEN}>"
END_TOKEN = f"</{TOKEN}>"
MP3_OUTPUT_FOLDER = os.path.join(FOLDER_NAME, PREFIX_NAME + "_MP3")
MERGE_OUTPUT_FOLDER = os.path.join(MP3_OUTPUT_FOLDER, 'merge')

client = texttospeech.TextToSpeechClient()

voice = texttospeech.VoiceSelectionParams(
    language_code=LANG, name=VOICE
)

# noinspection PyTypeChecker
audio_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.LINEAR16
)


def text2speech(string: str, out_path: str):
    # noinspection PyTypeChecker
    input_text = texttospeech.SynthesisInput(text=string)

    response = client.synthesize_speech(
        input=input_text, voice=voice, audio_config=audio_config
    )


    # The response's audio_content is binary.
    with open(out_path, "wb") as out:
        out.write(response.audio_content)

    time.sleep(10)


def main():
    with open(FILE_TXT_PATH, 'r') as file:
        file_txt = file.read()

    if not os.path.exists(MP3_OUTPUT_FOLDER):
        os.makedirs(MP3_OUTPUT_FOLDER, exist_ok=True)

    if not os.path.exists(MERGE_OUTPUT_FOLDER):
        os.makedirs(MERGE_OUTPUT_FOLDER, exist_ok=True)

    soup = BeautifulSoup(file_txt, "lxml")
    chapters = soup.find_all(TOKEN)
    assert len(re.findall(START_TOKEN, file_txt)) == len(re.findall(END_TOKEN, file_txt))

    chapters_text = [chapters[i].text for i in range(len(chapters))]
    chapters_text = [re.sub('(.+)(?<!\.)$', r'\1.', ch, flags=re.M) for ch in chapters_text]

    def name_builder(chp_number: str):
        return base_build_name(
            chp_number=int(chp_number),
            prefix=PREFIX_NAME,
            format_number_fn=base_format_number_fn(len(chapters)))

    print("Starting Generation ...")
    for i in trange(0, len(chapters)):
        params = CreateChapterParams(
            text2speech_fn=text2speech,
            chapter_str=chapters_text[i],
            chapter_number=i + 1,
            name_builder=name_builder,
            t2p_out_folder=MP3_OUTPUT_FOLDER,
            merge_out_folder=MERGE_OUTPUT_FOLDER,
            out_extension='mp3',
            max_size=2500
        )
        create_chapter(params)


if __name__ == '__main__':
    main()
