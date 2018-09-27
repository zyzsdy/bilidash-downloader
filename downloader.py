import os
import re
import time
import shutil
import requests
import threading
import copy

from urllib import parse

cache_dir = "./cache"
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)

class MulThreadDownload(threading.Thread):
    def __init__(self, url, startpos, endpos, f, headers):
        super(MulThreadDownload,self).__init__()
        self.url = url
        self.startpos = startpos
        self.endpos = endpos
        self.fd = f
        self.headers = copy.deepcopy(headers)

    def download(self):
        self.headers['range'] = "bytes=%s-%s" % (self.startpos, self.endpos)

        res = requests.get(self.url, headers=self.headers)

        self.fd.seek(self.startpos)
        self.fd.write(res.content)
        print("[Downloader] Thread finished: %s at %s" % (self.getName(), time.time()))

    def run(self):
        self.download()

def download(avid, item, threads):
    https_re_pattern = re.compile(r'^http')
    url = https_re_pattern.sub('https', item['BaseURL'])

    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36',
        'origin': 'https://www.bilibili.com',
        'referer': 'https://www.bilibili.com/video/av{}'.format(avid)
    }

    r = requests.head(url, headers=headers)

    if (r.status_code // 100 % 10) != 2:
        print('Unable to access representation item source. HTTP Code: {}'.format(r.status_code))
        exit(7)

    file_length = int(r.headers['Content-Length'])
    filename = parse.urlparse(url).path.split('/')[-1]

    if 'Content-Disposition' in r.headers.keys():
        filenames = re.search(r'filename="(.+?)"', r.headers['Content-Disposition'])

        if filenames:
            filename = filenames.group(1)
            print("Use the filename sent by the server.: {}".format(filename))

    temp_file_path = os.path.join(cache_dir, filename)



    # Start Download
    print('Threads number: {}'.format(threads))
    threading.BoundedSemaphore(threads)

    step = file_length // threads
    mtd_list = []
    start = 0
    end = -1

    # build output file
    tempf = open(temp_file_path, 'w')
    tempf.close()

    with open(temp_file_path, 'rb+') as f:
        fileno = f.fileno()

        while end < file_length - 1:
            start = end + 1
            end = start + step - 1
            if end > file_length:
                end = file_length
            
            dup = os.dup(fileno)
            fd = os.fdopen(dup, 'rb+', -1)
            t = MulThreadDownload(url, start, end, fd, headers)
            t.start()
            mtd_list.append(t)

        for i in mtd_list:
            i.join()

    return temp_file_path

def clean(downloaded_files):
    print("Cleanning.")
    for file in downloaded_files:
        os.remove(file)

def fullclean():
    print("Delete all cache file in cache directory.")
    shutil.rmtree(cache_dir)
    exit(0)