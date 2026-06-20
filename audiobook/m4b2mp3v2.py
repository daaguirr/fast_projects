import os
from environs import Env
import json
import re
import subprocess
from pathlib import Path

env = Env()
env.read_env()

with env.prefixed("M4B2MP3_"):
    INPUT_PATH = env.str("INPUT_PATH")
    FFMPEG_PATH = env.str("FFMPEG_PATH")
    OUTPUT_DIR = env.str("OUTPUT_DIR", "out")
    BITRATE = env.str("BITRATE", "128k")


def get_chapters(filepath: str) -> list[dict]:
    result = subprocess.run(
        [
            "ffprobe", "-i", filepath,
            "-print_format", "json",
            "-show_chapters",
            "-loglevel", "quiet",
        ],
        capture_output=True,
        text=True,
    )

    return json.loads(result.stdout)["chapters"]


def safe_filename(title: str) -> str:
    return re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')


def split_chapter(input_file: str, start: str, end: str, output: Path, title: str, track: int) -> None:
    ffmpeg_path = os.path.abspath(FFMPEG_PATH)

    subprocess.run(
        [
            ffmpeg_path, "-i", input_file,
            "-ss", start,
            "-to", end,
            "-vn",
            "-acodec", "libmp3lame",
            "-ab", BITRATE,
            "-map_metadata", "-1",
            "-metadata", f"title={title}",
            "-metadata", f"track={track}",
            str(output),
            "-y",
        ],
        stderr=subprocess.DEVNULL,
        check=True,
    )


def main() -> None:
    base_name = os.path.splitext(os.path.basename(INPUT_PATH))[0]
    out_folder = Path(os.path.join(OUTPUT_DIR, f"{base_name}_split"))
    out_folder.mkdir(parents=True, exist_ok=True)

    chapters = get_chapters(INPUT_PATH)
    total = len(chapters)

    print(f"Found {total} chapters on '{INPUT_PATH}'")

    for i, chapter in enumerate(chapters, start=1):
        start = chapter["start_time"]
        end = chapter["end_time"]
        title = chapter["tags"].get("title", f"Chapter {i}")

        output = OUTPUT_DIR / f"{safe_filename(title)}_{i:03d}.mp3"

        print(f"[{i}/{total}] {title} -> {output.name}")
        split_chapter(INPUT_PATH, start, end, output, title, i)

    print(f"\nReady. {total} files in '{out_folder}/'")


if __name__ == "__main__":
    main()
