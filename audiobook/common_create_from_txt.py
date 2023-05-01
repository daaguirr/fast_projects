# -*- coding: utf-8 -*-
import os
import typing as ty

from pydub import AudioSegment

from audiobook.utils import format_number


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


def my_format_number(n):
    return format_number(n, len(chapters))


def build_name(chp_number: str):
    return f"{PREFIX_NAME}{my_format_number(chp_number)}"
