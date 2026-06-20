import dataclasses
import math
import codecs
import os
import typing as ty
from functools import partial
from pathlib import Path

import bs4
from pydub import AudioSegment


def format_number(n: int, max_n: int):
    digits = math.floor(math.log10(max_n)) + 1
    return ("0" * digits + str(n))[-digits:]


def read_smil(file_path: str):
    with codecs.open(file_path, mode="r", encoding="iso-8859-1") as f:
        soup = bs4.BeautifulSoup(f.read(), "lxml")

    return soup


def audios_from_file(path: str):
    soup = read_smil(path)

    unique: ty.Set[str] = set()
    for a in soup.find_all('audio'):
        unique.add(a.get('src'))
    return list(unique)


def write_part_to_file(f: ty.TextIO, name: str, content: str):
    f.write(
        f"\n<part>\n<name>{name}</name>\n<content>\n{content}\n</content></part>\n"
    )
    f.flush()


def create_part(text2speech_fn: ty.Callable[[str, Path], ty.Any],
                content: str, file: ty.TextIO, out_path: Path,
                part_id: str):
    text2speech_fn(content, out_path)
    write_part_to_file(file, part_id, content)
    return out_path


def get_chunks(lines: ty.List[str], max_size: int):
    current = ''
    current_letter = 'a'
    for line in lines:
        if len(current) + len(line) > max_size:
            yield current, current_letter
            current = ''
            current_letter = chr(ord(current_letter) + 1)

        current = current + '\n' + line
    yield current, current_letter


@dataclasses.dataclass
class CreateChapterParams:
    text2speech_fn: ty.Callable[[str, Path], ty.Any]
    chapter_str: str
    chapter_number: str
    name_builder: ty.Callable[[str], str]
    t2p_out_folder: str
    merge_out_folder: str
    out_extension: str = 'wav'
    chunks_builder: ty.Callable[[list[str]], ty.Generator[tuple[str, str], None, None]] = partial(get_chunks,
                                                                                                  max_size=6500)
    max_size: int = 6800


def create_chapter(params: CreateChapterParams):
    lines = params.chapter_str.split(os.linesep)
    name_prefix = params.name_builder(params.chapter_number)

    files = []

    recovery_path = Path(params.t2p_out_folder) / f"{name_prefix}.txt"

    with open(recovery_path, "a", encoding="utf-8") as recovery_file:
        for chunk, current_letter in params.chunks_builder(lines):
            out_path = Path(params.t2p_out_folder) / f"{name_prefix}{current_letter}.{params.out_extension}"

            files.append(str(out_path))
            if out_path.exists() and out_path.stat().st_size > 0:
                print(f"Skipping existing part {params.chapter_number} {current_letter}")
                continue
            create_part(params.text2speech_fn, chunk, recovery_file, out_path, current_letter)

            recovery_file.flush()
            os.fsync(recovery_file.fileno())

    merge_chapter(params.chapter_number, files, params.merge_out_folder)


def merge_chapter(chapter_name: str, files: list[str], out_folder: str):
    output_file = Path(out_folder) / f"{chapter_name}.mp3"

    if output_file.exists() and output_file.stat().st_size > 0:
        print(f"Skipping merged chapter {chapter_name}")
        return str(output_file)

    playlist_songs = [AudioSegment.from_file(f) for f in files]
    combined = AudioSegment.empty()

    for song in playlist_songs:
        combined += song

    combined.export(
        output_file,
        format="mp3",
        bitrate="192k"
    )

    return str(output_file)


def base_format_number_fn(n_chapters: int):
    def inner(n: int):
        return format_number(n, n_chapters)

    return inner


def base_build_name(prefix: str, chp_number: int, format_number_fn: ty.Callable[[int], str]):
    return f"{prefix}{format_number_fn(chp_number)}"
