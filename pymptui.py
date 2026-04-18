from logging import config
import subprocess
import json
import os
import sys
import shutil
import curses

__version__ = "v2.0"


def get_latest_release_tag():
    try:
        url = "https://api.github.com/repos/cells-OSS/pymp/releases/latest"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data["tag_name"].lstrip("v")
    except Exception as e:
        print("Failed to check for updates:", e)
        return __version__.lstrip("v")


def is_update_available(current_version):
    latest = get_latest_release_tag()
    return version.parse(latest) > version.parse(current_version.lstrip("v"))


def download_latest_script():
    latest_version = get_latest_release_tag()
    filename = f"pymp-v{latest_version}.py"
    url = "https://raw.githubusercontent.com/cells-OSS/pymp/main/pymp.py"
    response = requests.get(url)
    lines = response.text.splitlines()
    with open(filename, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line.rstrip() + "\n")
    print(
        f"Current version: {__version__}, Latest: v{get_latest_release_tag()}")
    print(
        f"Downloaded update as '{filename}'. You can now safely delete the old version.")

    input("Press Enter to exit...")
    exit()


def download_youtube_mp3(youtube_url, output_path):
    try:
        yt_dlp_cmd = 'yt-dlp.exe' if os.name == 'nt' else 'yt-dlp'
        subprocess.run([
            yt_dlp_cmd,
            '-x', '--audio-format', 'mp3',
            '-o', output_path,
            youtube_url
        ], check=True)
        print(f"Audio downloaded and saved as {output_path}")
        input("Press Enter to continue...")
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")

def download_youtube_mp3_partial(youtube_url, output_path, start_time, end_time):
    """
    Download only a section as MP3 using yt-dlp's --download-sections and extract audio.
    start_time / end_time accept formats like SS, MM:SS or HH:MM:SS.
    """
    yt_dlp_cmd = 'yt-dlp.exe' if os.name == 'nt' else 'yt-dlp'
    ffmpeg_cmd = 'ffmpeg.exe' if os.name == 'nt' else 'ffmpeg'

    # normalize path, ensure .mp3 extension, create parent dir if possible
    output_path = os.path.expanduser(output_path)
    output_path = os.path.abspath(output_path)
    if not output_path.lower().endswith(".mp3"):
        output_path += ".mp3"
    parent = os.path.dirname(output_path) or "."

    if parent and not os.path.exists(parent):
        try:
            os.makedirs(parent, exist_ok=True)
        except PermissionError:
            print(f"Permission denied creating '{parent}'. Falling back to current directory.")
            output_path = os.path.basename(output_path)

    # require yt-dlp and ffmpeg (yt-dlp uses ffmpeg to extract)
    if shutil.which(yt_dlp_cmd) is None:
        print("yt-dlp not found. Please install yt-dlp and ensure it's on your PATH.")
        return
    if shutil.which(ffmpeg_cmd) is None:
        print("ffmpeg not found. Please install ffmpeg and ensure it's on your PATH.")
        return

    cmd = [
        yt_dlp_cmd,
        "--download-sections", f"*{start_time}-{end_time}",
        "-x", "--audio-format", "mp3",
        "-o", output_path,
        youtube_url
    ]
    try:
        subprocess.run(cmd, check=True)
        print(f"Trimmed audio saved to: {output_path}")
        input("Press Enter to continue...")
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except subprocess.CalledProcessError as e:
        print("yt-dlp failed:", e)
    except PermissionError as e:
        print("Permission error:", e)

def download_youtube_mp4(youtube_url, output_path):
    try:
        yt_dlp_cmd = 'yt-dlp.exe' if os.name == 'nt' else 'yt-dlp'
        subprocess.run([
            yt_dlp_cmd,
            '-f', 'mp4',
            '-o', output_path,
            youtube_url
        ], check=True)
        print(f"Video downloaded and saved as {output_path}")
        input("Press Enter to continue...")
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")

def download_youtube_mp4_partial(youtube_url, output_path, start_time, end_time):
    yt_dlp = "yt-dlp.exe" if os.name == "nt" else "yt-dlp"
    subprocess.run([yt_dlp, "--download-sections", f"*{start_time}-{end_time}", "-t", "mp4", "-o", output_path, youtube_url], check=True)
    print(f"Trimmed video downloaded and saved as {output_path}")
    input("Press Enter to continue...")
    os.execv(sys.executable, [sys.executable] + sys.argv)

def convert_mp4_to_mp3(input_file, output_file, bitrate="192k"):
    """
    Convert an MP4 (or other video file) to .mp3 using ffmpeg.
    Requires ffmpeg on PATH or ffmpeg.exe on Windows.
    """
    ffmpeg_cmd = 'ffmpeg.exe' if os.name == 'nt' else 'ffmpeg'
    if shutil.which(ffmpeg_cmd) is None:
        print("ffmpeg not found. Please install ffmpeg and ensure it's on your PATH.")
        return

    if not os.path.exists(input_file):
        print("Input file does not exist:", input_file)
        return

    if not output_file.lower().endswith(".mp3"):
        output_file += ".mp3"

    cmd = [
        ffmpeg_cmd,
        "-y",           # overwrite output without asking
        "-i", input_file,
        "-vn",          # no video
        "-ab", bitrate,  # audio bitrate
        "-ar", "44100",  # audio sampling rate
        output_file
    ]
    try:
        subprocess.run(cmd, check=True)
        print(f"Converted '{input_file}' -> '{output_file}'")
        input("Press Enter to continue...")
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except subprocess.CalledProcessError as e:
        print("ffmpeg failed:", e)


def install_packages(package):
    if os.name == 'nt':
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", package])
    else:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", package, "--break-system-packages"])


required_packages = ["yt-dlp", "requests", "packaging", "pyfiglet"]
for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        print(f"Installing required package {package}...")
        install_packages(package)

os.system('cls' if os.name == 'nt' else 'clear')

from packaging import version
import requests
import pyfiglet
import yt_dlp

if os.name == "nt":
    config_dir = os.path.join(os.getenv("APPDATA"), "pymp")
else:
    config_dir = os.path.expanduser("~/.config/pymp")

os.makedirs(config_dir, exist_ok=True)

config_path = os.path.join(config_dir, "config.json")

def menu(stdscr, title, options):
    curses.curs_set(0)
    stdscr.keypad(True)

    current = 0

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()

        # Title
        stdscr.addstr(1, w // 2 - len(title) // 2, title, curses.A_BOLD)

        # Options
        for i, option in enumerate(options):
            x = w // 2 - len(option) // 2
            y = h // 2 - len(options) // 2 + i

            if i == current:
                stdscr.addstr(y, x - 2, ">")
                stdscr.addstr(y, x, option, curses.A_REVERSE)
            else:
                stdscr.addstr(y, x, option)

        stdscr.refresh()

        key = stdscr.getch()

        if key == curses.KEY_UP:
            current = (current - 1) % len(options)
        elif key == curses.KEY_DOWN:
            current = (current + 1) % len(options)
        elif key in (curses.KEY_ENTER, 10, 13):
            return current

def mp3_menu(stdscr):
    options = ["Download", "Partial download", "Back"]

    while True:
        choice = menu(stdscr, "MP3", options)

        if options[choice] == "Back":
            return
        elif options[choice] == "Download":
            mp3_download_menu(stdscr)
        elif options[choice] == "Partial download":
            mp3_partial_download_menu(stdscr)

def mp4_menu(stdscr):
    options = ["Download", "Partial download", "Back"]

    while True:
        choice = menu(stdscr, "MP4", options)

        if options[choice] == "Back":
            return
        elif options[choice] == "Download":
            mp4_download_menu(stdscr)
        elif options[choice] == "Partial download":
            mp4_partial_download_menu(stdscr)

def mp3_download_menu(stdscr):

    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()

    url = input("Youtube URL: ")
    output = input("Output location and name: ")
    if output == "":
        output = "~/Downloads/audio"
    download_youtube_mp3(url, output + ".mp3")

def mp3_partial_download_menu(stdscr):

    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()

    url = input("Youtube URL: ")
    output = input("Output location and name: ")
    if output == "":
        output = "~/Downloads/audio"
    start_time = input("Enter the start time in seconds (or in HH:MM:SS): ")
    end_time = input("Enter the end time in seconds (or in HH:MM:SS): ")
    download_youtube_mp3_partial(url, output + ".mp3", start_time, end_time)

def mp4_download_menu(stdscr):

    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()

    url = input("Youtube URL: ")
    output = input("Output location and name: ")
    if output == "":
        output = "~/Downloads/video"
    download_youtube_mp4(url, output + ".mp4")

def mp4_partial_download_menu(stdscr):
    
    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()

    url = input("Youtube URL: ")
    output = input("Output location and name: ")
    if output == "":
        output = "~/Downloads/video"
    start_time = input("Enter the start time in seconds (or in HH:MM:SS): ")
    end_time = input("Enter the end time in seconds (or in HH:MM:SS): ")
    download_youtube_mp4_partial(url, output + ".mp4", start_time, end_time)

def mp43_menu(stdscr):

    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()

    input_file = input("MP4 file: ")
    output_file = input("Output location: ")

    convert_mp4_to_mp3(input_file, output_file)

def main_menu(stdscr):
    while True:
        choice = menu(
            stdscr,
            "Main Menu",
            ["Download MP3", "Download MP4", "MP4 -> MP3"]
        )

        if choice == 0:
            mp3_menu(stdscr)
        elif choice == 1:
            mp4_menu(stdscr)
        elif choice == 2:
            mp43_menu(stdscr)

def main(stdscr):
    main_menu(stdscr)

if __name__ == "__main__":
    curses.wrapper(main)
