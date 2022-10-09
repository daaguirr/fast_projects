# -*- coding: utf-8 -*-
import re
import typing as ty

import roman
from environs import Env

env = Env()
env.read_env()

with env.prefixed("CREATE_"):
    FILE_TXT_PATH = env.str("FILE_TXT_PATH")
    TOKEN = env.str("TOKEN")
    START_TOKEN = f"<{TOKEN}>\n"
    END_TOKEN = f"</{TOKEN}>\n"


def classic_format(multiple_books: bool):
    def inner(chapter: int, book_number: int):
        if multiple_books:
            return f"Libro {book_number} Capítulo {chapter}\n"
        else:
            return f"Capítulo {chapter}\n"

    return inner


def classic_chapter(match: re.Match):
    return int(match.group(1).rstrip())


def roman_chapter(match: re.Match):
    clean = match.group(1).rstrip()
    return roman.fromRoman(clean)


def regex_match(
        lines: list[str],
        regex: str,
        get_chapter: ty.Callable[[re.Match], int],
        title_format: ty.Callable[[int, int], str],
):
    current_book = 1
    last = 0
    new = [START_TOKEN]
    for line in lines:
        match = re.match(regex, line)
        if match:
            chapter_number = get_chapter(match)
            if chapter_number < last:
                current_book += 1
            print(line.rstrip(), current_book, chapter_number)
            new.append(END_TOKEN)
            new.append(START_TOKEN)
            new.append(title_format(chapter_number, current_book))
            last = chapter_number
        else:
            new.append(line)
    new.append(END_TOKEN)
    return new


roman_regex = r"(^(?=[MDCLXVI])M*(C[MD]|D?C{0,3})(X[CL]|L?X{0,3})(I[XV]|V?I{0,3})$)"
normal_regex = r'^(\d+)$'
prefix_regex = r"^Capítulo (\d+)$"


def main():
    with open(FILE_TXT_PATH) as f:
        data = f.readlines()

    new = regex_match(data, roman_regex, roman_chapter, classic_format(True))
    input("Press Enter to continue...")
    with open(FILE_TXT_PATH, "w") as f:
        f.write(''.join(new))


if __name__ == '__main__':
    main()
