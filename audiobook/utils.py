import math
import codecs
import bs4


def format_number(n, max_n):
    digits = math.floor(math.log10(max_n)) + 1
    return ("0" * digits + str(n))[-digits:]


def read_smil(file_path: str):
    with codecs.open(file_path, mode="r", encoding="iso-8859-1") as f:
        soup = bs4.BeautifulSoup(f.read(), "lxml")

    return soup


def audios_from_file(path):
    soup = read_smil(path)

    unique = set()
    for a in soup.find_all('audio'):
        unique.add(a.get('src'))
    unique = list(unique)
    return unique
