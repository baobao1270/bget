import argparse
import bgetlib
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class FolderConfig:
    danmaku_path: Optional[str] = None
    cover_path: Optional[str] = None
    meta_path: Optional[str] = None
    dash_path: Optional[str] = None
    aiff_path: Optional[str] = None
    flac_path: Optional[str] = None


@dataclass
class Config:
    id: int
    name: str
    cache_dir: str
    chunk_size: int
    cdn: Optional[str]
    folder: FolderConfig


class Runtime:
    from bgetcli.logger import Logger as _Logger

    def __init__(self, args: argparse.Namespace, config: Config, head: datetime, logger: _Logger):
        from bgetcli.utils import abspath
        self.out_dir = args.out
        self.skip = args.skip
        self.args = args
        self.head = head
        self.config = config
        self.logger = logger
        self.api = bgetlib.BilibiliAPI()
        self.downloader = bgetlib.Downloader()
        self.api.login(abspath(args.cookies))
        self.downloader.login(abspath(args.cookies))

    def head_timestamp(self) -> int:
        return int(self.head.timestamp())
