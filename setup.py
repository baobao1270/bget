from setuptools import setup, find_packages
import bgetcli.bget

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    install_requires = f.read().strip().replace("\r", "").split("\n")

setup(
    name="bget",
    version=bgetcli.bget.VERSION,
    description="bget - a python bilibili favourites batch downloader",
    long_description=long_description,
    long_description_content_type="text/markdown",
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
    package_data={'': ['LICENSE']},
    include_package_data=True,
    zip_safe=True,
    install_requires=install_requires,
    entry_points={
          'console_scripts': [
              'bget = bgetcli.bget:main'
          ]
    },
    project_urls={
        "Source": "https://github.com/baobao1270/bget.git",
    }
)
