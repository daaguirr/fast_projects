import os
import re
import shutil

root_dir = '/Users/tdc/Downloads/Torrent'


def to_folders():
    for file in os.listdir(root_dir):
        path = os.path.join(root_dir, file)
        if os.path.isfile(path):
            directory, file_extension = os.path.splitext(path)
            if file_extension in ['.avi', '.mkv', '.mp4']:
                if not os.path.exists(directory):
                    os.makedirs(directory)
                    shutil.move(path, os.path.join(directory, file))
                print(os.path.join(directory, file))


def process_item(item):
    regex_year = re.compile(r'.*((19|20)\d\d).*')
    clean = item.upper().replace('.', ' ').replace('_', ' ').replace('(', '').replace(')', '').replace('[',
                                                                                                       '').replace(
        ']', '')
    year_m = regex_year.match(clean)
    year = year_m.group(1) if year_m is not None else '-'

    for key in [year, ' ENG', 'XVID', 'BLURAY', 'X264', 'DVD', '1080P', '720P', '480P', '360P', 'BRRRIP', 'WEBRIP']:
        left = re.match(f'(.*){key}.*', clean)
        clean = left.group(1) if left is not None else clean
    clean = clean.strip(' ')
    return f'{clean} [{year}]'


def rename():
    for file in os.listdir(root_dir):
        path = os.path.join(root_dir, file)
        if os.path.isdir(path):
            # print(path)
            new_name = os.path.join(root_dir, process_item(file))
            os.rename(path, new_name)
            print(new_name)


def main():
    to_folders()
    rename()


if __name__ == '__main__':
    main()
