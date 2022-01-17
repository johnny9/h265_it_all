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

test_codec_command = 'ffmpeg -loglevel error ' \
                     '-f lavfi -i color=black:s=1080x1080 -vframes 1 ' \
                     '-an -c:v {codec} -f null -'


def is_a_videofile(filename: str) -> bool:
    for extension in video_extensions:
        if filename.endswith(extension):
            return True
    return False


def determine_codec() -> str:
    try:
        subprocess.run(test_codec_command.format(codec='hevc_nvenc'),
                       shell=True, check=True)
        return 'hevc_nvenc'
    except subprocess.CalledProcessError:
        pass

    try:
        subprocess.run(test_codec_command.format(codec='hevc_qsv'),
                       shell=True, check=True)
        return 'hevc_qsv'
    except subprocess.CalledProcessError:
        pass

    try:
        subprocess.run(test_codec_command.format(codec='hevc_vaapi'),
                       shell=True, check=True)
        return 'hevc_vaapi'
    except subprocess.CalledProcessError:
        pass

    return 'libx265'


def find_all_files(source_folder: str, condition) -> list:
    files = []
    source_path = Path(source_folder).expanduser()
    for item in source_path.iterdir():
        if item.is_file() and condition(item.name):
            files.append(item)
    return files


def new_bitrate(source: str):
    result = subprocess.run(bitrate_command.format(source=source),
                            shell=True, capture_output=True, text=True)
    return int(result.stdout) / 2


def convert_all_videos(source: str, destination: str, remove_old: bool):
    videos = find_all_files(source, is_a_videofile)
    codec = determine_codec()
    for video in videos:
        output = Path(destination, video.stem + '.mkv').expanduser()
        command_string = convert_command.format(source=video.absolute(),
                                                codec=codec,
                                                bitrate=new_bitrate(video),
                                                destination=output)
        print(command_string)
        subprocess.run(command_string, shell=True)
        if remove_old:
            video.unlink()


def move_other_files(source: str, destination: str, move: bool, remove: bool):
    if not move and not remove:
        return

    def not_a_video_file(filename: str):
        return not is_a_videofile(filename)
    files = find_all_files(source, not_a_video_file)
    for file in files:
        if move:
            destination_path = Path(destination, file.name).expanduser()
            file.replace(destination_path)
        elif remove:
            file.unlink()


def create_destination(destination: str):
    destination_path = Path(destination).expanduser()
    if not destination_path.exists():
        destination_path.mkdir(parents=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Convert all video files to h265'
    )
    parser.add_argument('-d', '--destination', required=True)
    parser.add_argument('-s', '--source', required=True)
    parser.add_argument('--dont-move-other-files', action='store_true')
    parser.add_argument('--remove-old-files', action='store_true')
    args = parser.parse_args()
    create_destination(args.destination.strip())
    convert_all_videos(args.source.strip(), args.destination.strip(),
                       args.remove_old_files)
    move_other_files(args.source.strip(), args.destination.strip(),
                     (not args.dont_move_other_files), args.remove_old_files)
