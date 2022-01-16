import argparse
import subprocess
from pathlib import Path


video_extensions = ['.mkv', '.avi', '.mp4']

convert_command = 'ffmpeg -i "{source}" -c:a copy -c:s copy ' \
                  '-c:v {codec} -preset slow -b:v {bitrate} ' \
                  '-y "{destination}"'

bitrate_command = 'ffprobe -i "{source}" -select_streams v:0 ' \
                  '-v quiet -show_entries format=bit_rate ' \
                  '-of default=noprint_wrappers=1:nokey=1'

nvenc_test_command = 'ffmpeg -loglevel error ' \
                     '-f lavfi -i color=black:s=1080x1080 -vframes 1 ' \
                     '-an -c:v hevc_nvenc -f null -'


def is_a_videofile(filename: str) -> bool:
    for extension in video_extensions:
        if filename.endswith(extension):
            return True
    return False


def is_nvenc_supported() -> bool:
    try:
        subprocess.run(nvenc_test_command, shell=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def determine_codec() -> str:
    if is_nvenc_supported():
        return 'hevc_nvenc'
    else:
        return 'libx265'


def find_all_video_files(source_folder: str) -> list:
    files = []
    source_path = Path(source_folder).expanduser()
    for item in source_path.iterdir():
        if item.is_file() and is_a_videofile(item.name):
            files.append(item)
    return files


def new_bitrate(source: str):
    result = subprocess.run(bitrate_command.format(source=source),
                            shell=True, capture_output=True, text=True)
    return int(result.stdout) / 2


def convert_all_videos(source: str, destination: str):
    videos = find_all_video_files(source)
    codec = determine_codec()
    for video in videos:
        output = Path(destination, video.stem + '.mkv').expanduser()
        command_string = convert_command.format(source=video.absolute(),
                                                codec=codec,
                                                bitrate=new_bitrate(video),
                                                destination=output)
        print(command_string)
        subprocess.run(command_string, shell=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Convert all video files to h265'
    )
    parser.add_argument('-d', '--destination', required=True)
    parser.add_argument('-s', '--source', required=True)
    args = parser.parse_args()
    convert_all_videos(args.source.strip(), args.destination.strip())
