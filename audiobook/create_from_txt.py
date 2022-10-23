# -*- coding: utf-8 -*-
import os
import re
import time
import typing as ty

from azure.cognitiveservices.speech import AudioDataStream, SpeechConfig, SpeechSynthesizer
from bs4 import BeautifulSoup
from environs import Env
from pydub import AudioSegment
from tqdm import trange

from utils import format_number

env = Env()
env.read_env()

with env.prefixed("CREATE_"):
    subscription_key = env.str("SUBSCRIPTION_KEY")
    region = env.str("REGION")
    FOLDER_NAME = env.str("OUTPUT_PATH")
    FILE_TXT_PATH = env.str("FILE_TXT_PATH")
    TOKEN = env.str("TOKEN")
    PREFIX_NAME = env.str("PREFIX_NAME")
    VOICE = env.str("VOICE")
    LANG = env.str("LANG")

START_TOKEN = f"<{TOKEN}>"
END_TOKEN = f"</{TOKEN}>"
WAV_OUTPUT_FOLDER = os.path.join(FOLDER_NAME, PREFIX_NAME + "_WAV")
MP3_OUTPUT_FOLDER = os.path.join(FOLDER_NAME, PREFIX_NAME + "_MP3")

speech_config = SpeechConfig(subscription=subscription_key, region=region)
synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=None)

with open(FILE_TXT_PATH, 'r') as file:
    file_txt = file.read()

if not os.path.exists(WAV_OUTPUT_FOLDER):
    os.makedirs(WAV_OUTPUT_FOLDER, exist_ok=True)

if not os.path.exists(MP3_OUTPUT_FOLDER):
    os.makedirs(MP3_OUTPUT_FOLDER, exist_ok=True)

build_name: ty.Callable[[str], str]


def text2speech(string, name):
    ssml_string = f"""
    <speak version="1.0" xmlns="https://www.w3.org/2001/10/synthesis" xml:lang="{LANG}">
        <voice name="{LANG}-{VOICE}">
            <prosody rate="0.9">
                <break time="200ms"/>
                    {string}
            </prosody>
        </voice>
    </speak>

    """
    result = synthesizer.speak_ssml_async(ssml_string).get()

    if result.cancellation_details:
        print(name, " = ", result.cancellation_details)
        input("Press Enter to continue...")

    stream = AudioDataStream(result)
    stream.save_to_wav_file(name)

    time.sleep(10)


def write_part_to_file(f: ty.TextIO, name: str, content: str):
    f.write(
        f"\n<part>\n<name>{name}</name>\n<content>\n{content}\n</content></part>\n"
    )
    f.flush()


def create_part(content: str, chapter_id: str, part_id: str, f: ty.TextIO):
    name_prefix = build_name(chapter_id)
    write_part_to_file(f, part_id, content)
    wav_path = os.path.join(WAV_OUTPUT_FOLDER, f"{name_prefix}{part_id}.wav")
    text2speech(content, wav_path)
    return os.path.join(WAV_OUTPUT_FOLDER, wav_path)


def create_chapter(chapter_str: str, chapter_number: str, max_size=6800):
    lines = chapter_str.split(os.linesep)
    current = ''
    current_letter = 'a'
    name_prefix = build_name(chapter_number)

    files = []
    f = open(os.path.join(WAV_OUTPUT_FOLDER, f"{name_prefix}.txt"), 'w')

    for line in lines:
        if len(current) + len(line) > max_size:
            files.append(create_part(current, chapter_number, current_letter, f))
            current = ''
            current_letter = chr(ord(current_letter) + 1)

        current = current + '\n' + line
    files.append(create_part(current, chapter_number, current_letter, f))
    f.close()
    merge_chapter(chapter_number, files)


def merge_chapter(chapter_name: str, files: list[str]):
    playlist_songs = [AudioSegment.from_wav(f) for f in files]
    combined = AudioSegment.empty()
    for song in playlist_songs:
        combined += song

    combined.export(os.path.join(MP3_OUTPUT_FOLDER, f"{chapter_name}.mp3"), format="mp3", bitrate="192k")


def main():
    global build_name
    soup = BeautifulSoup(file_txt, "lxml")
    chapters = soup.find_all(TOKEN)
    assert len(re.findall(START_TOKEN, file_txt)) == len(re.findall(END_TOKEN, file_txt))

    my_format_number = lambda n: format_number(n, len(chapters))
    build_name = lambda chp_number: f"{PREFIX_NAME}{my_format_number(chp_number)}"

    chapters_text = [chapters[i].text for i in range(len(chapters))]

    print("Starting Generation ...")
    for i in trange(0, len(chapters)):
        create_chapter(chapters_text[i], my_format_number(i + 1))


if __name__ == '__main__':
    main()
