import re
import os
import shutil
import argparse

from mpd import parseMpd
from downloader import download, clean, fullclean

parser = argparse.ArgumentParser(description='Download bilibili videos via DASH.')
parser.add_argument('html', help='Save html source to a file, then provide here.')
parser.add_argument('-F', '--list-formats', help='List formats without download.', action="store_true")
parser.add_argument('-f', '--format', help='Set download format id, eg. 16 or 18+20351.')
parser.add_argument('-o', '--output', help='Set output file.')
parser.add_argument('-t', '--threads', type=int, default=15, help='Number of download threads. Default to 15.')
parser.add_argument('--clean', help='Clean cache files.', action="store_true")
parser.add_argument('--version', action='version', version='0.1.0')

args = parser.parse_args()

def printFormats(video_reprs, audio_reprs):
    print("Video:")
    print("{:8s} {:15s} {:10s} {:s}".format('ID', 'Codecs', 'Bitrate', 'Size'))
    print("==========================================")
    for video_item in video_reprs:
        print("{:8s} {:15s} {:10s} {}x{}@{:.1f}".format(
            video_item['id'],
            video_item['codecs'],
            "{:.0f}Kbps".format(video_item['bandwidth'] / 1024.0),
            video_item['width'], video_item['height'], video_item['frameRate']
        ))
    print("Audio:")
    print("{:8s} {:15s} {:s}".format('ID', 'Codecs', 'Bitrate'))
    print("==========================================")
    for audio_item in audio_reprs:
        print("{:8s} {:15s} {:s}".format(
            audio_item['id'],
            audio_item['codecs'],
            "{:.0f}Kbps".format(audio_item['bandwidth'] / 1024.0)
        ))
    print()

def printReprItem(item):
    if 'video' in item['mimeType']:
        print("ID {}, Codecs {}, Bitrate {:.0f}Kbps, Size {}x{}@{:.1f}".format(
            item['id'],
            item['codecs'],
            item['bandwidth'] / 1024.0,
            item['width'], item['height'], item['frameRate']
        ))
    elif 'audio' in item['mimeType']:
        print("ID {}, Codecs {}, Bitrate {:.0f}Kbps".format(
            item['id'],
            item['codecs'],
            item['bandwidth'] / 1024.0
        ))
    else:
        print("Unrecognized representation")

def chooseDownload(video_reprs, audio_reprs):
    if args.format:
        format_list = args.format.split('+')
        if len(format_list) == 1:
            for k in video_reprs:
                if k['id'] == format_list[0]:
                    return [k]
            for k in audio_reprs:
                if k['id'] == format_list[0]:
                    return [k]
            print("Format id {} does not exist.".format(format_list[0]))
            exit(3)
        elif len(format_list) == 2:
            find_video = False
            find_audio = False
            for k in video_reprs:
                if k['id'] == format_list[0]:
                    video_item = k
                    find_video = True
            if not find_video:
                print("Format id {} does not exist in candidate videos.".format(format_list[0]))
                exit(4)
            for k in audio_reprs:
                if k['id'] == format_list[1]:
                    audio_item = k
                    find_audio = True
            if not find_audio:
                print("Format id {} does not exist in candidate audios.".format(format_list[1]))
                exit(5)
            return [video_item, audio_item]
        else:
            print("Format id cannot be parsed.")
            exit(2)
    else:
        return [video_reprs[-1], audio_reprs[-1]]

def main():
    with open(args.html, 'r', encoding='utf-8') as hf:
        source_text = hf.read()

    avids = re.search(r'"aid":(\d+?),', source_text)

    if avids:
        avid = avids.group(1)
        print('Source detected: https://www.bilibili.com/video/av{}'.format(avid))
    else:
        print("Unable to detect AV id from source.")
        exit(6)

    mpds = re.search(r'<\?xml.+</MPD>', source_text)

    if mpds:
        mpd = mpds.group(0)
    else:
        print("DASH-MPD was not found, it may not be logged in or no DASH source is provided.")
        exit(1)

    video_reprs, audio_reprs = parseMpd(mpd)
    if args.list_formats:
        printFormats(video_reprs, audio_reprs)
        exit(0)

    print("DASH-MPD has been found as parsed.")

    download_items = chooseDownload(video_reprs, audio_reprs)

    downloaded_files = []
    for download_item in download_items:
        print("Downloading...")
        printReprItem(download_item)
        df = download(avid, download_item, args.threads)
        downloaded_files.append(df)

    print("Merge:")
    if args.output:
        dest_file = os.path.join(os.getcwd(), args.output)
    else:
        dest_file = os.path.join(os.getcwd(), os.path.basename(downloaded_files[0]))
    if len(downloaded_files) == 1:
        dest_file = os.path.splitext(dest_file)[0] + '.mp4'
        shutil.copyfile(downloaded_files[0], dest_file)
    elif len(downloaded_files) == 2:
        dest_file = os.path.splitext(dest_file)[0] + '.mkv'
        s = os.system('mkvmerge -o "{}" {} {}'.format(dest_file, downloaded_files[0], downloaded_files[1]))

        if s >> 8 != 0:
            print("mkvmerge exit with error {}. please check manually in cache path: {}".format(s >> 8, os.path.realpath('./cache')))

        clean(downloaded_files)
    else:
        print("No file or More than 2 files are downloaded, please check manually in cache path: {}".format(os.path.realpath('./cache')))

    print("Successful.")


if __name__ == '__main__':
    mkvmerge_check = os.popen('mkvmerge --version')
    mkvmerge_version = mkvmerge_check.read()

    if len(mkvmerge_version) == 0:
        print('Please install "mkvmerge" and place it in the path directory.')
        exit(30)
    else:
        print("Successfully detected mkvmerge: {}".format(mkvmerge_version))

    if args.clean:
        fullclean()

    main()