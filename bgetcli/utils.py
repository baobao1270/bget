import copy
import dataclasses
import os
import toml
import argparse
from os import path
from datetime import datetime
from typing import Tuple, Optional
from bgetcli.const import WINDOWS_ESCAPE_CHARS, OUT
from bgetcli.logger import Logger
from bgetcli.model import Config, FolderConfig, Runtime


def abspath(name, base: Optional[str] = None):
    if base is None:
        base = os.getcwd()
    return path.abspath(path.join(base, name))


def win_escape(src: str) -> str:
    dest = src
    for search, replace in WINDOWS_ESCAPE_CHARS.items():
        dest = dest.replace(search, replace)
    return dest


def read_config(logger: Logger, args: argparse.Namespace) -> Tuple[Config, datetime]:
    config_path = abspath(args.config)
    config_base = path.dirname(config_path)
    config_toml = toml.load(config_path)
    head_path = abspath(args.head)
    logger.log("Loaded config: {}".format(abspath(args.config)))
    logger.log("Using HEAD file: {}".format(head_path))

    folder = config_toml[args.alias]
    config = Config(
        id=config_toml[args.alias]["id"],
        name=args.alias,
        cache_dir=abspath(config_toml.get("cache-dir") or "./tmp", base=config_base),
        chunk_size=(config_toml.get("chunk-size") or 4096),
        cdn=config_toml.get("cdn"),
        folder=FolderConfig(
            danmaku_path=folder.get("danmaku") is True or None,
            cover_path=folder.get("cover") is True or None,
            meta_path=folder.get("meta") is True or None,
            dash_path=folder.get("dash") is True or None,
            aiff_path=folder.get("aiff") is True or None,
            flac_path=folder.get("flac") is True or None,
        )
    )

    head: datetime = datetime.fromtimestamp(86400)
    if path.exists(head_path):
        head = toml.load(head_path).get(args.alias) or head
    return config, head


def outdirs_init(rt: Runtime):
    OUTDIRS = OUT.DIR()
    OUTDIRS.DANMAKU = abspath(OUT.DIR.DANMAKU.format(out_dir=rt.out_dir, name=rt.config.name))
    OUTDIRS.COVER = abspath(OUT.DIR.COVER.format(out_dir=rt.out_dir, name=rt.config.name))
    OUTDIRS.META = abspath(OUT.DIR.META.format(out_dir=rt.out_dir, name=rt.config.name))
    OUTDIRS.DASH = abspath(OUT.DIR.DASH.format(out_dir=rt.out_dir, name=rt.config.name))
    OUTDIRS.AIFF = abspath(OUT.DIR.AIFF.format(out_dir=rt.out_dir, name=rt.config.name))
    OUTDIRS.FLAC = abspath(OUT.DIR.FLAC.format(out_dir=rt.out_dir, name=rt.config.name))
    return OUTDIRS


def dest_path(rt: Runtime, filename_template: str, **kwargs):
    # noinspection PyPep8Naming,SpellCheckingInspection
    OUTDIRS = outdirs_init(rt)
    out_dir = {
        OUT.FILENAME.DANMAKU: OUTDIRS.DANMAKU,
        OUT.FILENAME.COVER:   OUTDIRS.COVER,
        OUT.FILENAME.META:    OUTDIRS.META,
        OUT.FILENAME.DASH:    OUTDIRS.DASH,
        OUT.FILENAME.AIFF:    OUTDIRS.AIFF,
        OUT.FILENAME.FLAC:    OUTDIRS.FLAC,

    }[filename_template]
    filename = filename_template.format(**kwargs)
    return "{}/{}".format(out_dir, filename)


def class2dict(clazz):
    data = copy.copy(clazz.__dict__)
    for k, v in clazz.__dict__.items():
        if dataclasses.is_dataclass(v):
            data[k] = copy.copy(v.__dict__)
        if isinstance(v, list):
            data[k] = [copy.copy(i.__dict__) for i in v]
    return data

