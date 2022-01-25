# bget
bget - a python bilibili favourites batch downloader

## Install
```bash
pip install bget
```

## Use
 1. Download [config.toml](https://github.com/baobao1270/bget/blob/master/config-example.toml) and edit it as your need.
 2. Get your bilibili.com cookies. You can use [this chrome extension (Get cookies.txt)](https://chrome.google.com/webstore/detail/get-cookiestxt/bgaddhkoddajcdgocldbbfleckgcbcid).
 3. Use `bget -h` to get help:

## Build
We use a fake "makefile" to build.

```bash
python -m venv venv
venv\Scripts\activate
pip3 install pyyaml
make build
```

## License
MIT License
