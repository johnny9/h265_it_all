import argparse
from pathlib import Path 

video_extensions = ['.mkv', '.avi', '.mp4']

def is_a_videofile(filename: str) -> bool:
	for extension in video_extensions:
		if filename.endswith(extension):
			return True
	return False

def find_all_video_files(source_folder: str) -> list:
	files = []
	source_path = Path(source_folder).expanduser()
	for item in source_path.iterdir():
		if item.is_file() and is_a_videofile(item.name):
			files.append(item)
	return files

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Convert all video files to h265')
	parser.add_argument('-d', '--destination')
	parser.add_argument('-s', '--source')
	args = parser.parse_args()
	videos = find_all_video_files(args.source.strip())
	print(videos)