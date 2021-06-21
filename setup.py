import bgetcli.const
from setuptools import setup, find_packages

VERSION = bgetcli.const.VERSION

setup(
    name="bget",
    version=VERSION,
    description="bget - a python bilibili favourites batch downloader",
    long_description="See: https://github.com/baobao1270/bget",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    keywords="python bilibili terminal",
    author="Joseph Chris",
    author_email="joseph@josephcz.xyz",
    url="https://github.com/baobao1270/bget",
    license="MIT",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=True,
    install_requires=[
        "requests",
        "bgetlib",
        "toml"
    ],
    entry_points={
          'console_scripts': [
              'bget = bgetcli.bget:main'
          ]
    },
    project_urls={
        "Source": "https://github.com/baobao1270/bget.git",
    }
)
