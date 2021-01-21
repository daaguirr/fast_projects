# -*- coding: utf-8 -*-
import math
import os
import re

from azure.cognitiveservices.speech import AudioDataStream, SpeechConfig, SpeechSynthesizer
from bs4 import BeautifulSoup
from environs import Env
from tqdm import trange

env = Env()
env.read_env()

with env.prefixed("CREATE_"):
    subscription_key = env.str("SUBSCRIPTION_KEY")
    region = env.str("REGION")
    FOLDER_NAME = env.str("OUTPUT_WAV_PATH")
    FILE_TXT_PATH = env.str("FILE_TXT_PATH")
    START_TOKEN = env.str("START_TOKEN")
    END_TOKEN = env.str("END_TOKEN")
    PREFIX_NAME = env.str("PREFIX_NAME")

speech_config = SpeechConfig(subscription=subscription_key, region=region)
synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=None)

with open(FILE_TXT_PATH, 'r') as file:
    file_txt = file.read()

assert len(re.findall(START_TOKEN, file_txt)) == len(re.findall(END_TOKEN, file_txt))

soup = BeautifulSoup(file_txt, "lxml")
chapters = soup.find_all('chapter')

for i in range(len(chapters)):
    chapters[i] = chapters[i].text

print(len(chapters), chapters)


def format_number(n, max_n):
    digits = math.floor(math.log10(max_n)) + 1
    return ("0" * digits + str(n))[-digits:]


my_format_number = lambda n: format_number(n, len(chapters))
build_name = lambda chp_number: os.path.join(FOLDER_NAME, f"{PREFIX_NAME}{my_format_number(chp_number)}")


def create_chapter(chapter_str, chapter_number):
    lines = chapter_str.split('\n')
    current = ''
    current_letter = 'a'
    name_prefix = build_name(chapter_number)

    with open(f"{name_prefix}.txt", 'w') as f:
        for line in lines:
            new_size = len(line)
            if len(current) + new_size > 7250:
                print(current_letter)
                f.write(
                    f"\n<part>\n<name>{current_letter}</name>\n<content>\n{current}\n</content></part>\n"
                )
                process(current, f"{name_prefix}{current_letter}.wav")
                current = ''
                current_letter = chr(ord(current_letter) + 1)

            current = current + '\n' + line
        print(current_letter)
        f.write(
            f"\n<part>\n<name>{current_letter}</name>\n<content>\n{current}\n</content></part>\n"
        )
        process(current, f"{name_prefix}{current_letter}.wav")


def process(string, name):
    ssml_string = f"""
    <speak version="1.0" xmlns="https://www.w3.org/2001/10/synthesis" xml:lang="es-MX">
        <voice name="es-MX-DaliaNeural">
            <prosody rate="0.9">
                <break time="200ms"/>
                    {string}
            </prosody>
        </voice>
    </speak>

    """
    result = synthesizer.speak_ssml(ssml_string)

    stream = AudioDataStream(result)
    stream.save_to_wav_file(name)


if __name__ == '__main__':
    for i in trange(len(chapters)):
        create_chapter(chapters[i], i + 1)
