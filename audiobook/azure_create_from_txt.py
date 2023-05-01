# -*- coding: utf-8 -*-
import os
import re
import time

from azure.cognitiveservices.speech import AudioDataStream, SpeechConfig, SpeechSynthesizer
from bs4 import BeautifulSoup
from environs import Env
from tqdm import trange

from utils import CreateChapterParams, base_format_number_fn, base_build_name, create_chapter

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

    time.sleep(5)


def main():
    with open(FILE_TXT_PATH, 'r') as file:
        file_txt = file.read()

    if not os.path.exists(WAV_OUTPUT_FOLDER):
        os.makedirs(WAV_OUTPUT_FOLDER, exist_ok=True)

    if not os.path.exists(MP3_OUTPUT_FOLDER):
        os.makedirs(MP3_OUTPUT_FOLDER, exist_ok=True)

    soup = BeautifulSoup(file_txt, "lxml")
    chapters = soup.find_all(TOKEN)
    assert len(re.findall(START_TOKEN, file_txt)) == len(re.findall(END_TOKEN, file_txt))

    chapters_text = [chapters[i].text for i in range(len(chapters))]

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
            t2p_out_folder=WAV_OUTPUT_FOLDER,
            merge_out_folder=MP3_OUTPUT_FOLDER,
            out_extension='wav',
            max_size=6500
        )
        create_chapter(params)


if __name__ == '__main__':
    main()
