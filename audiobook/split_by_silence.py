import subprocess
import re
import os
from datetime import timedelta
from environs import Env

env = Env()
env.read_env()

with env.prefixed("SPLIT_BY_SILENCE_"):
    INPUT_PATH = env.str("INPUT_PATH")
    OUT_FOLDER = env.str("OUT_FOLDER", default="out")
    UMBRAL_DB = env.int("UMBRAL_DB", default=-40)
    MIN_DURATION = env.int("MIN_DURATION", default=3)


def extract_timestamps(lines: list[str], pattern: str) -> list[float]:
    return [
        float(m.group(1))
        for line in lines
        if (m := re.search(pattern, line))
    ]


def parse_silences(stdout: str) -> list[float]:
    lines = stdout.split('\n')
    starts = extract_timestamps(lines, r'silence_start: ([\d.]+)')
    ends = extract_timestamps(lines, r'silence_end: ([\d.]+)')

    return [(s + e) / 2 for s, e in zip(starts, ends)]


def detect_silences(input_file: str, umbral_db: float, duration_min: float):
    cmd_detect = [
        'ffmpeg', '-i', input_file,
        '-af', f'silencedetect=n={umbral_db}dB:d={duration_min}',
        '-f', 'null', '-'
    ]
    result = subprocess.run(cmd_detect, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True)

    return parse_silences(result.stdout)


def split_command(input_file: str, start_of_interval: float, duration: float | None, out_file: str) -> list[str]:
    cmd_args = [
        ('-i', input_file),
        ('-ss', start_of_interval),
        ('-t', duration),
        ('-c', 'copy'),
        ('-y', out_file)
    ]
    cmd_args = [a for a in cmd_args if a[1] is not None]
    flat_args = [str(item) for a in cmd_args for item in a]

    return ['ffmpeg'] + flat_args


def split_by_silence(input_file, umbral_db=-40, duration_min=3,
                     out_folder: str = "out"):
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    out_folder = os.path.join(out_folder, f"{base_name}_split")

    os.makedirs(out_folder, exist_ok=True)

    # Step 1: Detect silences
    print("Detecting silences...")
    split_points: list[float] = [0] + detect_silences(input_file, umbral_db, duration_min)

    print(f"Found {len(split_points)} chapters")
    input("Press Enter to continue...")

    # Step 2: Split
    for i in range(len(split_points)):
        start_of_interval = split_points[i]

        out_file = os.path.join(out_folder,
                                f"{base_name}_{i + 1:03d}.mp3")

        if i < len(split_points) - 1:
            end_of_interval = split_points[i + 1]
            duration = end_of_interval - start_of_interval
        else:
            duration = None

        cmd_cut = split_command(input_file, start_of_interval, duration, out_file)

        timestamp = timedelta(seconds=start_of_interval)

        print(f"Part {i + 1} (from {timestamp})...", end=" ")
        subprocess.run(cmd_cut, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("✓")

    print(f"\nFinished! {len(split_points)} files in: {out_folder}/")


# Uso
if __name__ == "__main__":
    split_by_silence(INPUT_PATH,
                     umbral_db=UMBRAL_DB, duration_min=MIN_DURATION, out_folder=OUT_FOLDER)
