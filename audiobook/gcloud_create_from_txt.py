# -*- coding: utf-8 -*-
import json
import os
import re
import time
import typing
import uuid
from functools import partial

from bs4 import BeautifulSoup
from environs import Env
from google.cloud import texttospeech
from tqdm import trange

from utils import create_chapter, CreateChapterParams, base_build_name, base_format_number_fn
from google.oauth2 import service_account
from pathlib import Path

env = Env()
env.read_env()

with env.prefixed("CREATE_"):
    FOLDER_NAME: str = env.str("OUTPUT_PATH")
    FILE_TXT_PATH = env.str("FILE_TXT_PATH")
    TOKEN = env.str("TOKEN")
    PREFIX_NAME = env.str("PREFIX_NAME")
    VOICE = env.str("VOICE")
    LANG = env.str("LANG")

START_TOKEN = f"<{TOKEN}>"
END_TOKEN = f"</{TOKEN}>"
MP3_OUTPUT_FOLDER = os.path.join(FOLDER_NAME, PREFIX_NAME + "_MP3")
MERGE_OUTPUT_FOLDER = os.path.join(MP3_OUTPUT_FOLDER, 'merge')

credentials = service_account.Credentials.from_service_account_file(
    ".credentials/apis-311920-sa.json"
)

client = texttospeech.TextToSpeechClient(credentials=credentials)

voice = texttospeech.VoiceSelectionParams(
    language_code=LANG, name=VOICE,
    # model_name="gemini-2.5-flash-tts",
)

# noinspection PyTypeChecker
audio_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.LINEAR16,
    speaking_rate=1.0,
)


def text2speech(string: str, out_path: Path):
    # noinspection PyTypeChecker
    input_text = texttospeech.SynthesisInput(
        text=string,
        # prompt="Lee estilo audiolibro"
    )

    try:
        response = client.synthesize_speech(
            input=input_text, voice=voice, audio_config=audio_config
        )

    except Exception as e:
        print(string)
        print(e)

        raise e

    # The response's audio_content is binary.
    with open(out_path, "wb") as out:
        out.write(response.audio_content)

    time.sleep(10)


def _next_label(i: int) -> str:
    s = ''
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(ord('a') + r) + s
    return s


def smart_text_chunker(
        lines: list[str],
        max_bytes: int = 4500,
        encoding: str = 'utf-8',
        prefer_sentence_breaks: bool = True,
        safety_margin: int = 200
) -> typing.Generator[tuple[str, str], None, None]:
    max_size = max_bytes - safety_margin
    current = ''
    current_letter = 'a'

    for line in lines:
        line = line.strip()
        if not line:
            continue

        potential_text = (current + '\n' + line) if current else line
        potential_bytes = len(potential_text.encode(encoding))

        if potential_bytes <= max_size:
            current = potential_text
            continue

        # overflow
        if current:
            yield current.strip(), current_letter
            current_letter = chr(ord(current_letter) + 1)

        current = line

        if len(current.encode(encoding)) > max_size:
            for sub_chunk in _split_long_line(
                    current, max_size, encoding, prefer_sentence_breaks
            ):
                yield sub_chunk, current_letter
                current_letter = chr(ord(current_letter) + 1)
            current = ''

    if current.strip():
        yield current.strip(), current_letter


def _split_long_line(
        text: str,
        max_bytes: int,
        encoding: str = 'utf-8',
        prefer_sentence_breaks: bool = True
) -> typing.Generator[str, None, None]:
    if len(text.encode(encoding)) <= max_bytes:
        yield text
        return

    if not prefer_sentence_breaks:
        for word_chunk in _split_by_words(text, max_bytes, encoding):
            yield word_chunk
        return

    sentences = _split_into_sentences(text)
    current = ''

    for sentence in sentences:
        potential = (current + ' ' + sentence) if current else sentence

        if len(potential.encode(encoding)) <= max_bytes:
            current = potential
            continue

        # overflow
        if current:
            yield current.strip()

        current = sentence

        if len(current.encode(encoding)) > max_bytes:
            for word_chunk in _split_by_words(sentence, max_bytes, encoding):
                yield word_chunk
            current = ''

    if current:
        yield current.strip()


def _split_into_sentences(
        text: str,
        protected_abbrevs: typing.Optional[list[str]] = None
) -> list[str]:
    if not text.strip():
        return []

    protected_abbrevs = protected_abbrevs or ['etc']
    replacements = {}

    # Protección de abreviaciones
    def protect_abbrev(match):
        key = f'__ABBR_{uuid.uuid4().hex[:8]}__'
        replacements[key] = match.group(0)
        return key

    pattern = r'(' + '|'.join(re.escape(a) + r'\.' for a in protected_abbrevs) + r')'
    protected_text = re.sub(pattern, protect_abbrev, text, flags=re.IGNORECASE)

    # División en oraciones más robusta
    sentences = re.split(r'(?<=[.!?])\s+', protected_text)
    sentences = [s.strip() for s in sentences if s.strip()]

    # Restaurar abreviaciones
    restored = []
    for s in sentences:
        for placeholder, original in replacements.items():
            s = s.replace(placeholder, original)
        restored.append(s)

    return restored or [text.strip()]


def _split_by_words(
        text: str,
        max_bytes: int,
        encoding: str = 'utf-8'
) -> typing.Generator[str, None, None]:
    words = text.split()
    current = ''

    for word in words:
        potential = (current + ' ' + word) if current else word

        if len(potential.encode(encoding)) <= max_bytes:
            current = potential
            continue

        # overflow
        if current:
            yield current.strip()

        current = word

        if len(current.encode(encoding)) > max_bytes:
            raise Exception(f'Invalid word {word}')

    if current:
        yield current.strip()


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
    chapters_text = [re.sub(r'(.+)(?<!\.)$', r'\1.', ch, flags=re.M) for ch in chapters_text]

    def name_builder(chp_number: str):
        return base_build_name(
            chp_number=int(chp_number),
            prefix=PREFIX_NAME,
            format_number_fn=base_format_number_fn(len(chapters)))

    print("Starting Generation ...")

    for i in trange(len(chapters)):
        params = CreateChapterParams(
            text2speech_fn=text2speech,
            chapter_str=chapters_text[i],
            chapter_number=i + 1,
            name_builder=name_builder,
            t2p_out_folder=MP3_OUTPUT_FOLDER,
            merge_out_folder=MERGE_OUTPUT_FOLDER,
            out_extension='mp3',
            chunks_builder=partial(
                smart_text_chunker,
                max_bytes=3800,
                encoding='utf-8',
                prefer_sentence_breaks=True,
                safety_margin=200
            )
        )
        create_chapter(params)


if __name__ == '__main__':
    main()
