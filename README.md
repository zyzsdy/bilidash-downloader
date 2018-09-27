# BILIDASH-DOWNLOADER

## 安装

Python 3.5+
Mkvmerge (尽量高的版本)

请把mkvmerge放到path里

python依赖

```bash
pip install lxml requests
```

## 用法

在需要下载的播放页上右键，选择“查看网页源代码”，然后把所有内容保存在temp.html中。

接下来运行
```bash
python bdd.py temp.html
```
即可下载

如果希望先查询格式列表，你可以使用
```bash
python bdd.py -F temp.html
```
命令

找到需要的格式后，使用
```bash
python bdd.py -f <格式代码> temp.html
```
或者
```bash
python bdd.py -f <视频格式代码>+<音频格式代码> temp.html
```
下载

更多参数请查看
```bash
python bdd.py -h
```

## LICENSE
MIT