import glob
import os
import subprocess

from environs import Env

env = Env()
env.read_env()

with env.prefixed("M4B2MP3_"):
    INPUT_PATH = env.str("INPUT_PATH")
    FFMPEG_PATH = env.str("FFMPEG_PATH")


def main():
    base_dir = os.path.abspath(INPUT_PATH)
    ffmpeg_path = os.path.abspath(FFMPEG_PATH)

    pattern = os.path.join(base_dir, '**', '*.m4b')

    file_list = [file for file in glob.glob(pattern, recursive=True)]

    for file in file_list:
        dir_path, file_name = os.path.split(file)
        # Drop the file extension
        file_name = os.path.splitext(file_name)[0]
        output_path = os.path.join(dir_path, file_name + '.mp3')

        if not os.path.exists(output_path):
            # Convert
            print('Converting: ' + file)
            subprocess.call(
                [ffmpeg_path, '-i', file, '-codec:v', 'copy', '-codec:a', 'libmp3lame', '-q:a', '2', output_path])
        else:
            print('Skipping: ' + file)


if __name__ == "__main__":
    main()
