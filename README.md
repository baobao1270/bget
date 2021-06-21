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
    ```
    usage: bget [OPTIONS] <section>
    
    bget - a python bilibili favourites batch downloader
    
    positional arguments:
      <section>             section name of favourite in config file
    
    optional arguments:
      -h, --help            show this help message and exit
      -s <offset>, --skip <offset>
                            skip <offset> videos form start (default: 0)
      -k <cookies>, --cookies <cookies>
                            cookies file path (default: bilibili.com_cookies.txt)
      -c <config>, --config <config>
                            config file path (default: config.toml)
      -t <head>, --head <head>
                            head file path (default: head.toml)
      -o <output-folder>, --out <output-folder>
                            download output folder path (default: downloads)
      -v, --version         show program's version number and exit
    ```

## Build
```bash
python setup.py sdist bdist_wheel

# if want to upload to pypi
twine upload dist/bget-<version>*
```

To clear all rubbish, use `clear_all.bat`.

## License
MIT
